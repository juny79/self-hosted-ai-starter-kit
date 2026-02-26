def format_time(timestamp):
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

def save_to_file(data, filename):
    with open(filename, 'w') as file:
        file.write(data)