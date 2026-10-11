"""Bounded read-only trace of the pinned warning input chain."""
SITES = {270: 0x40f12a, 271: 0x40f12f, 272: 0x40f165,
         273: 0x40f16b, 274: 0x40f180, 275: 0x40f246,
         276: 0x40f24c, 277: 0x40f2d0}


def arm(driver):
    for index, address in SITES.items():
        driver.command(f'bp{index} {address:x}')


def capture(index, event, driver):
    event['event_type'] = 'WARNING_INPUT_TRACE'
    data = {'registers': driver.command('r'), 'stack': driver.command('dd @esp L18')}
    if index == 270:
        data['input'] = driver.command('da poi(@esp) L100')
        data['format'] = driver.command('da poi(@esp+4) L20')
    elif index == 271:
        data['parsed_path'] = driver.command('da poi(@esp+8) L100')
        data['parsed_numbers'] = driver.command('dd poi(@esp+c) L1; dd poi(@esp+10) L1')
    elif index == 272:
        data['root_path'] = driver.command('da poi(@esp) L20')
        data['slot'] = driver.command('dd 57040c L1')
        data['module'] = driver.command('lm m ddraw')
        data['target'] = driver.command('u poi(57040c) L20')
        data['outputs_before'] = driver.command('dd poi(@esp+4) L1; dd poi(@esp+8) L1; dd poi(@esp+c) L1; dd poi(@esp+10) L1')
    elif index == 273:
        data['outputs_after'] = driver.command('dd @esp+24 L4')
    elif index == 275:
        data['branch'] = driver.command('u @eip L2')
    event['warning_input'] = data
    return index == 276
