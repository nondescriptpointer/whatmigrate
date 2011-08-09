# Humanize bytes
def humanize(length,precision=1):
    abbrevs = (
        (1<<50L, 'PB'),
        (1<<40L, 'TB'),
        (1<<30L, 'GB'),
        (1<<20L, 'MB'),
        (1<<10L, 'kB'),
        (1,'bytes')
    )
    if length == 1:
        return '1 byte'
    for factor, suffix in abbrevs:
        if length >= factor:
            break
    return '%.*f %s' % (precision, length / factor, suffix)
