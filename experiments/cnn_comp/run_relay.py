from validate_config import validate
from exp_templates import (common_trial_params, common_early_exit, run_template)
from relay_util import cnn_setup, cnn_trial, cnn_teardown

if __name__ == '__main__':
    run_template(validate_config=validate,
                 check_early_exit=common_early_exit({'frameworks': 'relay'}),
                 gen_trial_params=common_trial_params(
                     'relay', 'cnn_comp',
                     cnn_trial, cnn_setup, cnn_teardown,
                     ['network', 'device', 'batch_size', 'opt_level'],
                     ['networks', 'devices', 'batch_sizes', 'relay_opt']))
