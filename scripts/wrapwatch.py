"""lldb helper: log every frame/bounds change of RNSScreenContentWrapper and RNSScreenView.

Usage: see scripts/trace.sh.
"""
import lldb

STATE = {'wrapper': 0, 'screen': 0, 'out': '/tmp/wrapwatch.txt'}


def _log(text):
    with open(STATE['out'], 'a') as f:
        f.write(text + '\n')


def arm(debugger, command, result, internal_dict):
    """Install the probes once UIApplicationMain runs (classes are registered by then)."""
    if command.strip():
        STATE['out'] = command.strip()
    open(STATE['out'], 'w').close()
    target = debugger.GetSelectedTarget()
    b = target.BreakpointCreateByName('UIApplicationMain')
    b.SetScriptCallbackFunction('wrapwatch.on_main')
    b.SetOneShot(True)
    b.SetAutoContinue(True)


def on_main(frame, bp_loc, extra_args, internal_dict):
    _install(frame.GetThread().GetProcess().GetTarget(), frame)
    return False


def install(debugger, command, result, internal_dict):
    """Install the probes into an already running, stopped process."""
    if command.strip():
        STATE['out'] = command.strip()
    open(STATE['out'], 'w').close()
    target = debugger.GetSelectedTarget()
    _install(target, target.GetProcess().GetSelectedThread().GetSelectedFrame())


def _isa(proc, ptr):
    err = lldb.SBError()
    isa = proc.ReadPointerFromMemory(ptr, err)
    if not err.Success():
        return 0
    return isa & 0x0000000ffffffff8


def _install(target, frame):
    _expr(frame, '@import UIKit')
    STATE['wrapper'] = frame.EvaluateExpression(
        '(unsigned long)objc_getClass("RNSScreenContentWrapper")').GetValueAsUnsigned()
    STATE['screen'] = frame.EvaluateExpression(
        '(unsigned long)objc_getClass("RNSScreenView")').GetValueAsUnsigned()
    STATE['lm_off'] = frame.EvaluateExpression(
        '(long)ivar_getOffset((Ivar)class_getInstanceVariable((Class)objc_getClass("RCTViewComponentView"), "_layoutMetrics"))').GetValueAsSigned()
    _log('classes wrapper=%x screen=%x lm_off=%d' % (STATE['wrapper'], STATE['screen'], STATE['lm_off']))
    for name in ['-[UIView setBounds:]', '-[UIView setFrame:]']:
        b = target.BreakpointCreateByName(name)
        b.SetScriptCallbackFunction('wrapwatch.geom_cb')
        b.SetAutoContinue(True)
    b = target.BreakpointCreateByName('-[RNSScreenContentWrapper updateLayoutMetrics:oldLayoutMetrics:]')
    b.SetScriptCallbackFunction('wrapwatch.metrics_cb')
    b.SetAutoContinue(True)
    b = target.BreakpointCreateByName('-[UIView setTranslatesAutoresizingMaskIntoConstraints:]')
    b.SetScriptCallbackFunction('wrapwatch.tamic_cb')
    b.SetAutoContinue(True)
    for name in ['+[NSLayoutConstraint activateConstraints:]', '+[NSLayoutConstraint deactivateConstraints:]']:
        b = target.BreakpointCreateByName(name)
        b.SetScriptCallbackFunction('wrapwatch.constraints_cb')
        b.SetAutoContinue(True)
    b = target.BreakpointCreateByName('-[RNSScreenStackHeaderConfig prepareForRecycle]')
    b.SetScriptCallbackFunction('wrapwatch.config_recycle_cb')
    b.SetAutoContinue(True)
    b = target.BreakpointCreateByName('-[RCTViewComponentView prepareForRecycle]')
    b.SetScriptCallbackFunction('wrapwatch.recycle_cb')
    b.SetAutoContinue(True)


def _rect_at(proc, addr):
    err = lldb.SBError()
    data = proc.ReadMemory(addr, 32, err)
    if not err.Success():
        return '?'
    import struct
    return '(%g %g; %g %g)' % struct.unpack('<4d', data)


def _stack(thread, depth):
    names = []
    for i in range(1, min(depth, thread.GetNumFrames())):
        n = thread.GetFrameAtIndex(i).GetFunctionName() or '?'
        names.append(n[:100] if not n.startswith('std::') else n.split('::$')[0][-60:])
    return ' <- '.join(names)


def geom_cb(frame, bp_loc, extra_args, internal_dict):
    proc = frame.GetThread().GetProcess()
    x0 = frame.FindRegister('x0').GetValueAsUnsigned()
    isa = _isa(proc, x0)
    if isa == STATE['wrapper']:
        kind = 'W'
    elif isa == STATE['screen']:
        kind = 'S'
    else:
        return False
    d = [frame.FindRegister('d%d' % i).GetValue() for i in range(4)]
    sel = 'setBounds' if 'Bounds' in frame.GetFunctionName() else 'setFrame '
    _log('%s %x %s (%s %s; %s %s)  %s' % (kind, x0, sel, d[0], d[1], d[2], d[3],
                                          _stack(frame.GetThread(), 6)))
    return False


def _expr(frame, text):
    opts = lldb.SBExpressionOptions()
    opts.SetLanguage(lldb.eLanguageTypeObjC_plus_plus)
    opts.SetTimeoutInMicroSeconds(2000000)
    return frame.EvaluateExpression(text, opts)


def _wstate(frame, x0):
    proc = frame.GetThread().GetProcess()
    cache = _rect_at(proc, x0 + STATE['lm_off'])
    tamic = _expr(frame, '(int)[(UIView *)%d translatesAutoresizingMaskIntoConstraints]' % x0).GetValueAsSigned()
    h = _expr(frame, '(double)[(UIView *)%d bounds].size.height' % x0).GetValue()
    sup = _expr(frame, '(unsigned long)[(UIView *)%d superview]' % x0).GetValueAsUnsigned()
    win = _expr(frame, '(int)([(UIView *)%d window] != nil)' % x0).GetValueAsSigned()
    return 'cache=%s h=%s tamic=%d super=%x win=%d' % (cache, h, tamic, sup, win)


def metrics_cb(frame, bp_loc, extra_args, internal_dict):
    proc = frame.GetThread().GetProcess()
    x0 = frame.FindRegister('x0').GetValueAsUnsigned()
    x2 = frame.FindRegister('x2').GetValueAsUnsigned()
    x3 = frame.FindRegister('x3').GetValueAsUnsigned()
    _log('W %x updateLayoutMetrics new=%s old=%s | %s' % (x0, _rect_at(proc, x2), _rect_at(proc, x3), _wstate(frame, x0)))
    return False


def recycle_cb(frame, bp_loc, extra_args, internal_dict):
    proc = frame.GetThread().GetProcess()
    x0 = frame.FindRegister('x0').GetValueAsUnsigned()
    if _isa(proc, x0) != STATE['wrapper']:
        return False
    _log('W %x prepareForRecycle | %s' % (x0, _wstate(frame, x0)))
    return False


def tamic_cb(frame, bp_loc, extra_args, internal_dict):
    proc = frame.GetThread().GetProcess()
    x0 = frame.FindRegister('x0').GetValueAsUnsigned()
    if _isa(proc, x0) != STATE['wrapper']:
        return False
    x2 = frame.FindRegister('x2').GetValueAsUnsigned() & 0xff
    _log('W %x tAMIC=%d  %s' % (x0, x2, _stack(frame.GetThread(), 3)))
    return False


def constraints_cb(frame, bp_loc, extra_args, internal_dict):
    caller = frame.GetThread().GetFrameAtIndex(1).GetFunctionName() or ''
    if 'RNSScreenStackHeaderConfig' not in caller:
        return False
    x2 = frame.FindRegister('x2').GetValueAsUnsigned()
    kind = 'activate' if 'deactivate' not in frame.GetFunctionName() else 'deactivate'
    count = frame.EvaluateExpression('(unsigned long)[(NSArray *)%d count]' % x2).GetValueAsUnsigned() if x2 else 0
    first = frame.EvaluateExpression('(unsigned long)[[(NSArray *)%d firstObject] firstItem]' % x2).GetValueAsUnsigned() if count else 0
    _log('C %s n=%d wrapper=%x  %s' % (kind, count, first, caller[:80]))
    return False


def config_recycle_cb(frame, bp_loc, extra_args, internal_dict):
    x0 = frame.FindRegister('x0').GetValueAsUnsigned()
    _log('C %x config prepareForRecycle' % x0)
    return False


def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f wrapwatch.install wrapwatch_install')
    debugger.HandleCommand('command script add -f wrapwatch.arm wrapwatch_arm')
