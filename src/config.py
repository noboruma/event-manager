import configparser
import email_utils

def get_config(config_file):
    config = configparser.ConfigParser()
    config.read(config_file)
    config_service = config['service']
    return (config_service['db_file'],
            config_service['secret_token'],
            email_utils.Context(config_service['smtp_host'],
                config_service['smtp_port'], config_service['sender_email'],
                config_service.get('sender_pass', None)))
