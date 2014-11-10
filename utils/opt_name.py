def opt_name(s, prefix):
    assert '.' in s
    i = -1
    while s[i] != '.':
        i = i - 1
    old_ext = s[i:]
    return s[-len(s): i] + prefix + old_ext

filename = 'cubo4x4.bot.etch.nc'
print 'original = ', filename
print 'mod      = ', opt_name(filename, '.OPT')
