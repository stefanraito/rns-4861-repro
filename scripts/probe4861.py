"""lldb probe for react-native-screens#4861.

Logs, for RNSScreenContentWrapper / RNSScreenStackHeaderConfig:
  - every +[RNSScreenStackHeaderConfig updateViewController:withConfig:animated:] call
    (vc, its view, view.subviews[0], config, config._show, config._safeAreaConstraints[0].firstItem)
  - every config updateProps / prepareForRecycle / removeFromSuperview (with _screenView, superview)
  - every wrapper tAMIC change, mount into an RNSScreenView, prepareForRecycle
  - every wrapper setBounds coming from UIKit's Auto Layout engine (_applyISEngineLayoutValuesToBoundsOnly:)

Usage (attached to a stopped process):
  command script import scripts/probe4861.py
  probe_install /tmp/probe.txt
  process continue
"""
import struct

import lldb

S = {'out': '/tmp/probe.txt'}


def log(text):
    with open(S['out'], 'a') as f:
        f.write(text + '\n')


def ev(frame, text):
    opts = lldb.SBExpressionOptions()
    opts.SetLanguage(lldb.eLanguageTypeObjC_plus_plus)
    opts.SetTimeoutInMicroSeconds(3000000)
    opts.SetTryAllThreads(False)
    return frame.EvaluateExpression(text, opts)


def u(frame, text):
    return ev(frame, text).GetValueAsUnsigned()


def isa(proc, ptr):
    if not ptr:
        return 0
    err = lldb.SBError()
    v = proc.ReadPointerFromMemory(ptr, err)
    return (v & 0x0000000ffffffff8) if err.Success() else 0


def rd_ptr(proc, addr):
    err = lldb.SBError()
    v = proc.ReadPointerFromMemory(addr, err)
    return v if err.Success() else 0


def rd_u8(proc, addr):
    err = lldb.SBError()
    v = proc.ReadUnsignedFromMemory(addr, 1, err)
    return v if err.Success() else -1


def rd_rect(proc, addr):
    err = lldb.SBError()
    data = proc.ReadMemory(addr, 32, err)
    if not err.Success():
        return '?'
    return '(%g %g; %g %g)' % struct.unpack('<4d', data)


def kind(proc, ptr):
    c = isa(proc, ptr)
    if c == S['W']:
        return 'W'
    if c == S['C']:
        return 'C'
    if c == S['SV']:
        return 'SV'
    return '?'


def tag(frame, ptr):
    if not ptr:
        return 0
    return ev(frame, '(long)[(UIView *)%d tag]' % ptr).GetValueAsSigned()


def wdesc(frame, w):
    proc = frame.GetThread().GetProcess()
    tamic = ev(frame, '(int)[(UIView *)%d translatesAutoresizingMaskIntoConstraints]' % w).GetValueAsSigned()
    h = ev(frame, '(double)[(UIView *)%d bounds].size.height' % w).GetValue()
    sup = u(frame, '(unsigned long)[(UIView *)%d superview]' % w)
    supk = kind(proc, sup)
    suph = ev(frame, '(double)[(UIView *)%d bounds].size.height' % sup).GetValue() if sup else '-'
    cache = rd_rect(proc, w + S['lm_off'])
    return 'W%x(tag %d) tamic=%d h=%s cache=%s super=%s%x(tag %d,h %s)' % (
        w, tag(frame, w), tamic, h, cache, supk, sup, tag(frame, sup), suph)


def caller(frame, depth=4):
    th = frame.GetThread()
    names = []
    for i in range(1, min(depth + 1, th.GetNumFrames())):
        n = th.GetFrameAtIndex(i).GetFunctionName() or '?'
        if n.startswith('std::'):
            n = n.split('::$')[0][-50:]
        names.append(n[:90])
    return ' <- '.join(names)


def sac_first(frame, cfg):
    proc = frame.GetThread().GetProcess()
    arr = rd_ptr(proc, cfg + S['sac_off'])
    if not arr:
        return 0, 0
    n = u(frame, '(unsigned long)[(NSArray *)%d count]' % arr)
    if not n:
        return arr, 0
    return arr, u(frame, '(unsigned long)[[(NSArray *)%d firstObject] firstItem]' % arr)


# ---------------------------------------------------------------- callbacks

def _cb_update_vc(frame, bp_loc, extra, d):
    proc = frame.GetThread().GetProcess()
    vc = frame.FindRegister('x2').GetValueAsUnsigned()
    cfg = frame.FindRegister('x3').GetValueAsUnsigned()
    view = u(frame, '(unsigned long)[(UIViewController *)%d view]' % vc)
    nsub = u(frame, '(unsigned long)[[(UIView *)%d subviews] count]' % view)
    sub0 = u(frame, '(unsigned long)[[(UIView *)%d subviews] firstObject]' % view) if nsub else 0
    nav = u(frame, '(unsigned long)[(UIViewController *)%d parentViewController]' % vc)
    show = rd_u8(proc, cfg + S['show_off']) if cfg else -1
    transl = rd_u8(proc, cfg + S['transl_off']) if cfg else -1
    arr, first = sac_first(frame, cfg) if cfg else (0, 0)
    sv = rd_ptr(proc, cfg + S['sv_off']) if cfg else 0
    flags = []
    if cfg and first and sub0 and first != sub0 and kind(proc, sub0) == 'W':
        flags.append('MISMATCH(sac.first=%x sub0=%x)' % (first, sub0))
    if cfg and sv and sv != view:
        flags.append('CFG_SCREENVIEW!=VC.VIEW(%x)' % sv)
    log('U updateVC vc=%x view=%s%x(tag %d) nav=%x sub0=%s%x cfg=C%x(tag %d) show=%d transl=%d sac=%x first=%x %s | %s' % (
        vc, kind(proc, view), view, tag(frame, view), nav, kind(proc, sub0), sub0, cfg, tag(frame, cfg),
        show, transl, arr, first, ' '.join(flags), caller(frame, 3)))
    return False


def _cb_cfg_props(frame, bp_loc, extra, d):
    proc = frame.GetThread().GetProcess()
    cfg = frame.FindRegister('x0').GetValueAsUnsigned()
    sv = rd_ptr(proc, cfg + S['sv_off'])
    sup = u(frame, '(unsigned long)[(UIView *)%d superview]' % cfg)
    flag = 'STALE_SCREENVIEW' if sv and sv != sup else ''
    log('C%x(tag %d) updateProps screenView=%x super=%x show=%d %s' % (
        cfg, tag(frame, cfg), sv, sup, rd_u8(proc, cfg + S['show_off']), flag))
    return False


def _cb_cfg_recycle(frame, bp_loc, extra, d):
    proc = frame.GetThread().GetProcess()
    cfg = frame.FindRegister('x0').GetValueAsUnsigned()
    sv = rd_ptr(proc, cfg + S['sv_off'])
    sup = u(frame, '(unsigned long)[(UIView *)%d superview]' % cfg)
    arr, first = sac_first(frame, cfg)
    log('C%x(tag %d) prepareForRecycle screenView=%x super=%x sac=%x first=%x' % (
        cfg, tag(frame, cfg), sv, sup, arr, first))
    return False


def _cb_cfg_rfs(frame, bp_loc, extra, d):
    proc = frame.GetThread().GetProcess()
    cfg = frame.FindRegister('x0').GetValueAsUnsigned()
    if kind(proc, cfg) != 'C':
        return False
    log('C%x(tag %d) removeFromSuperview screenView=%x' % (cfg, tag(frame, cfg), rd_ptr(proc, cfg + S['sv_off'])))
    return False


def _cb_tamic(frame, bp_loc, extra, d):
    proc = frame.GetThread().GetProcess()
    w = frame.FindRegister('x0').GetValueAsUnsigned()
    if kind(proc, w) != 'W':
        return False
    v = frame.FindRegister('x2').GetValueAsUnsigned() & 0xff
    log('W%x setTAMIC(%d) before: %s | %s' % (w, v, wdesc(frame, w), caller(frame, 2)))
    return False


def _cb_mount(frame, bp_loc, extra, d):
    proc = frame.GetThread().GetProcess()
    sv = frame.FindRegister('x0').GetValueAsUnsigned()
    child = frame.FindRegister('x2').GetValueAsUnsigned()
    k = kind(proc, child)
    if k == 'W':
        tamic = ev(frame, '(int)[(UIView *)%d translatesAutoresizingMaskIntoConstraints]' % child).GetValueAsSigned()
        flag = 'LEAKED_TAMIC_NO' if tamic == 0 else ''
        log('M SV%x(tag %d) mount W%x(tag %d) tamic=%d %s' % (sv, tag(frame, sv), child, tag(frame, child), tamic, flag))
    elif k == 'C':
        log('M SV%x(tag %d) mount C%x(tag %d) cfg.screenView(before)=%x' % (
            sv, tag(frame, sv), child, tag(frame, child), rd_ptr(proc, child + S['sv_off'])))
    return False


def _cb_unmount(frame, bp_loc, extra, d):
    proc = frame.GetThread().GetProcess()
    sv = frame.FindRegister('x0').GetValueAsUnsigned()
    child = frame.FindRegister('x2').GetValueAsUnsigned()
    k = kind(proc, child)
    if k in ('W', 'C'):
        log('M SV%x(tag %d) unmount %s%x(tag %d)' % (sv, tag(frame, sv), k, child, tag(frame, child)))
    return False


def _cb_recycle(frame, bp_loc, extra, d):
    proc = frame.GetThread().GetProcess()
    w = frame.FindRegister('x0').GetValueAsUnsigned()
    if kind(proc, w) != 'W':
        return False
    log('W%x prepareForRecycle %s' % (w, wdesc(frame, w)))
    return False


def _cb_setbounds(frame, bp_loc, extra, d):
    proc = frame.GetThread().GetProcess()
    w = frame.FindRegister('x0').GetValueAsUnsigned()
    if kind(proc, w) != 'W':
        return False
    log('E W%x engine apply (boundsOnly=%d)  before: %s | %s' % (
        w, frame.FindRegister('x2').GetValueAsUnsigned() & 0xff, wdesc(frame, w), caller(frame, 40)))
    return False


def _cb_wlm(frame, bp_loc, extra, d):
    proc = frame.GetThread().GetProcess()
    w = frame.FindRegister('x0').GetValueAsUnsigned()
    x2 = frame.FindRegister('x2').GetValueAsUnsigned()
    x3 = frame.FindRegister('x3').GetValueAsUnsigned()
    log('L W%x layoutMetrics new=%s old=%s' % (w, rd_rect(proc, x2), rd_rect(proc, x3)))
    return False




# ---------------------------------------------------------------- safe wrappers
import traceback


def _safe(fn):
    def w(frame, bp_loc, extra, d):
        try:
            fn(frame, bp_loc, extra, d)
        except Exception:
            log('!! %s: %s' % (fn.__name__, traceback.format_exc().replace('\n', ' | ')))
        return False
    return w


cb_update_vc = _safe(_cb_update_vc)
cb_cfg_props = _safe(_cb_cfg_props)
cb_cfg_recycle = _safe(_cb_cfg_recycle)
cb_cfg_rfs = _safe(_cb_cfg_rfs)
cb_tamic = _safe(_cb_tamic)
cb_mount = _safe(_cb_mount)
cb_unmount = _safe(_cb_unmount)
cb_recycle = _safe(_cb_recycle)
cb_setbounds = _safe(_cb_setbounds)
cb_wlm = _safe(_cb_wlm)


# ---------------------------------------------------------------- install

def _bp(target, name, fn):
    b = target.BreakpointCreateByName(name)
    b.SetScriptCallbackFunction('probe4861.' + fn)
    b.SetAutoContinue(True)
    if b.GetNumLocations() == 0:
        log('!! no locations for ' + name)
    return b


def _ivar(frame, cls, name):
    return ev(frame, '(long)ivar_getOffset((Ivar)class_getInstanceVariable((Class)objc_getClass("%s"), "%s"))' % (
        cls, name)).GetValueAsSigned()


def install(debugger, command, result, internal_dict):
    args = command.split()
    light = 'light' in args
    minimal = 'minimal' in args
    args = [a for a in args if a not in ('light', 'minimal')]
    wlm_only = 'wlm' in args
    args = [a for a in args if a != 'wlm']
    if args:
        S['out'] = args[0]
    open(S['out'], 'w').close()
    target = debugger.GetSelectedTarget()
    frame = target.GetProcess().GetSelectedThread().GetSelectedFrame()
    ev(frame, '@import UIKit')
    S['W'] = u(frame, '(unsigned long)objc_getClass("RNSScreenContentWrapper")')
    S['C'] = u(frame, '(unsigned long)objc_getClass("RNSScreenStackHeaderConfig")')
    S['SV'] = u(frame, '(unsigned long)objc_getClass("RNSScreenView")')
    S['lm_off'] = _ivar(frame, 'RCTViewComponentView', '_layoutMetrics')
    S['sac_off'] = _ivar(frame, 'RNSScreenStackHeaderConfig', '_safeAreaConstraints')
    S['sv_off'] = _ivar(frame, 'RNSScreenStackHeaderConfig', '_screenView')
    S['show_off'] = _ivar(frame, 'RNSScreenStackHeaderConfig', '_show')
    S['transl_off'] = _ivar(frame, 'RNSScreenStackHeaderConfig', '_translucent')
    log('init %s' % S)
    if wlm_only:
        _bp(target, '-[RNSScreenContentWrapper updateLayoutMetrics:oldLayoutMetrics:]', 'cb_wlm')
        return
    if minimal:
        _bp(target, '-[UIView setTranslatesAutoresizingMaskIntoConstraints:]', 'cb_tamic')
        _bp(target, '-[RNSScreenContentWrapper updateLayoutMetrics:oldLayoutMetrics:]', 'cb_wlm')
        return
    _bp(target, '+[RNSScreenStackHeaderConfig updateViewController:withConfig:animated:]', 'cb_update_vc')
    if not light:
        _bp(target, '-[RNSScreenStackHeaderConfig updateProps:oldProps:]', 'cb_cfg_props')
    _bp(target, '-[RNSScreenStackHeaderConfig prepareForRecycle]', 'cb_cfg_recycle')
    _bp(target, '-[RNSScreenStackHeaderConfig removeFromSuperview]', 'cb_cfg_rfs')
    _bp(target, '-[UIView setTranslatesAutoresizingMaskIntoConstraints:]', 'cb_tamic')
    _bp(target, '-[RNSScreenView mountChildComponentView:index:]', 'cb_mount')
    _bp(target, '-[RNSScreenView unmountChildComponentView:index:]', 'cb_unmount')
    if light:
        return
    _bp(target, '-[RCTViewComponentView prepareForRecycle]', 'cb_recycle')
    _bp(target, '-[UIView(Geometry) _applyISEngineLayoutValuesToBoundsOnly:]', 'cb_setbounds')
    _bp(target, '-[RNSScreenContentWrapper updateLayoutMetrics:oldLayoutMetrics:]', 'cb_wlm')


def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f probe4861.install probe_install')
