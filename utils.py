import psutil

def get_time_formatted(time):
    if time < 10800:
        return f"{int(time / 60)} minutes"
    else:
        return f"{(time / 3600):.1f} hours"
    
def get_running_process_names():
    names = set()
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name']:
                names.add(proc.info['name'].lower())
                #print(proc.info['name'].lower())
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return names