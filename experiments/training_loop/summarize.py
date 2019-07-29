import argparse

from validate_config import validate
from common import (write_status, write_summary, sort_data, render_exception)

def render_summary(devs, epochs, data):
    ret = 'Format: ({}) epochs\n'.format(', '.join([str(count) for count in epochs]))
    for dev in devs:
        ret += '_Times on {}_\n'.format(dev.upper())
        for (setting, times) in data[dev].items():
            ret += '{}: '.format(setting)
            ret += ', '.join(['{:.3f}'.format(time*1e3)
                              for (_, time) in times.items()])
            ret += '\n'
    return ret

def main(data_dir, config_dir, output_dir):
    config, msg = validate(config_dir)
    if config is None:
        write_status(output_dir, False, msg)
        return

    try:
        all_data = sort_data(data_dir)
        most_recent = all_data[-1]
        title = config['title']
        devs = config['devices']
        epochs = config['epochs']
        summary = render_summary(devs, epochs, most_recent)
        write_summary(output_dir, title, summary)
        write_status(output_dir, True, 'success')
    except Exception as e:
        write_status(output_dir, False, 'Exception encountered:\n' + render_exception(e))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, required=True)
    parser.add_argument("--config-dir", type=str, required=True)
    parser.add_argument("--output-dir", type=str, required=True)
    args = parser.parse_args()
    main(args.data_dir, args.config_dir, args.output_dir)