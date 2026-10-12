"""lldb helper: list every live RNSScreenContentWrapper (mounted or sitting in Fabric's recycle pool).

For each wrapper prints tAMIC, frame, Fabric's cached frame, superview, and, when the superview is an
RNSScreenView, whether that screen's header config is visible. Flags:
  LEAK   tAMIC == NO while not mounted (in the recycle pool)
  BAD    tAMIC == NO on a screen whose header is hidden or translucent
  SHORT  native frame height differs from Fabric's cached frame height
Usage: command script import scripts/scanwrappers.py ; scanwrappers [extra wrapper pointers...]
Scans wrappers found in all windows (plus any pointers passed explicitly).
"""
import re
import struct

import lldb


def ev(frame, text):
    opts = lldb.SBExpressionOptions()
    opts.SetLanguage(lldb.eLanguageTypeObjC_plus_plus)
    opts.SetTimeoutInMicroSeconds(5000000)
    return frame.EvaluateExpression(text, opts)


def scan(debugger, command, result, internal_dict):
    target = debugger.GetSelectedTarget()
    proc = target.GetProcess()
    frame = proc.GetSelectedThread().GetSelectedFrame()
    ev(frame, '@import UIKit')
    lm_off = ev(frame, '(long)ivar_getOffset((Ivar)class_getInstanceVariable((Class)objc_getClass("RCTViewComponentView"), "_layoutMetrics"))').GetValueAsSigned()
    show_off = ev(frame, '(long)ivar_getOffset((Ivar)class_getInstanceVariable((Class)objc_getClass("RNSScreenStackHeaderConfig"), "_show"))').GetValueAsSigned()
    transl_off = ev(frame, '(long)ivar_getOffset((Ivar)class_getInstanceVariable((Class)objc_getClass("RNSScreenStackHeaderConfig"), "_translucent"))').GetValueAsSigned()
    sv_cls = ev(frame, '(unsigned long)objc_getClass("RNSScreenView")').GetValueAsUnsigned()
    desc = ev(frame, '(NSString *)[[[UIApplication sharedApplication] valueForKeyPath:@"windows.recursiveDescription"] componentsJoinedByString:@"\\n"]').GetObjectDescription() or ''
    text = desc
    ptrs = sorted(set(int(m, 16) for m in re.findall(r'<RNSScreenContentWrapper: (0x[0-9a-f]+)', desc)))
    extra = command.split()
    ptrs += [int(x, 16) for x in extra if x.startswith('0x')]
    out = []
    err = lldb.SBError()
    for w in ptrs:
        cls = ev(frame, '(const char *)object_getClassName((id)%d)' % w).GetSummary() or ''
        if 'RNSScreenContentWrapper' not in cls:
            continue
        tamic = ev(frame, '(int)[(UIView *)%d translatesAutoresizingMaskIntoConstraints]' % w).GetValueAsSigned()
        h = ev(frame, '(double)[(UIView *)%d bounds].size.height' % w).GetValue()
        y = ev(frame, '(double)[(UIView *)%d frame].origin.y' % w).GetValue()
        data = proc.ReadMemory(w + lm_off, 32, err)
        cache = struct.unpack('<4d', data) if err.Success() else (0, 0, 0, 0)
        sup = ev(frame, '(unsigned long)[(UIView *)%d superview]' % w).GetValueAsUnsigned()
        win = ev(frame, '(int)([(UIView *)%d window] != nil)' % w).GetValueAsSigned()
        tag = ev(frame, '(long)[(UIView *)%d tag]' % w).GetValueAsSigned()
        flags = []
        cfgdesc = ''
        if sup:
            isa = proc.ReadPointerFromMemory(sup, err) & 0x0000000ffffffff8
            if isa == sv_cls:
                cfg = ev(frame, '(unsigned long)[(id)%d findHeaderConfig]' % sup).GetValueAsUnsigned()
                if cfg:
                    show = proc.ReadUnsignedFromMemory(cfg + show_off, 1, err)
                    transl = proc.ReadUnsignedFromMemory(cfg + transl_off, 1, err)
                    cfgdesc = 'cfg show=%d transl=%d' % (show, transl)
                    if tamic == 0 and (not show or transl):
                        flags.append('BAD')
                else:
                    cfgdesc = 'no cfg'
        elif tamic == 0:
            flags.append('LEAK')
        if h is not None and cache[3] > 0 and abs(float(h) - cache[3]) > 0.5:
            flags.append('SHORT')
        out.append('W %x tag=%d tamic=%d frame.y=%s h=%s cache=(%g %g; %g %g) super=%x win=%d %s %s' % (
            w, tag, tamic, y, h, cache[0], cache[1], cache[2], cache[3], sup, win, cfgdesc, ' '.join(flags)))
    result.AppendMessage('\n'.join(out) if out else 'no wrappers found:\n' + text[:2000])


def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand('command script add -f scanwrappers.scan scanwrappers')
