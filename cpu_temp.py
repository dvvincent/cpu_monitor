#!/usr/bin/env python3

import psutil
import time
from collections import defaultdict

def get_detailed_cpu_temperatures():
    try:
        # Try to read temperature from thermal sensors
        temps = psutil.sensors_temperatures()
        if not temps:
            return "Temperature sensors not found"
        
        results = defaultdict(list)
        
        # Look for CPU temperature in different possible sensor names
        for name, entries in temps.items():
            if any(x in name.lower() for x in ['cpu', 'coretemp', 'k10temp', 'acpitz']):
                for entry in entries:
                    # Get label, current temp, high temp and critical temp if available
                    label = entry.label or 'CPU'
                    current = f"{entry.current:.2f}°C"
                    high = f"{entry.high:.2f}°C" if entry.high is not None else "N/A"
                    critical = f"{entry.critical:.2f}°C" if entry.critical is not None else "N/A"
                    
                    results[name].append({
                        'label': label,
                        'current': current,
                        'high': high,
                        'critical': critical
                    })
        
        if not results:
            return "CPU temperature sensors not found"
            
        return results
    
    except Exception as e:
        return f"Error reading temperature: {str(e)}"

def format_temperature_output(temps):
    if isinstance(temps, str):
        return temps
        
    output = ["CPU Temperature Details:"]
    for sensor_name, readings in temps.items():
        output.append(f"\n{sensor_name}:")
        for reading in readings:
            output.append(
                f"  {reading['label']}:\n"
                f"    Current:  {reading['current']}\n"
                f"    High:     {reading['high']}\n"
                f"    Critical: {reading['critical']}"
            )
    return "\n".join(output)

def main():
    temps = get_detailed_cpu_temperatures()
    print(format_temperature_output(temps))

if __name__ == "__main__":
    main()
