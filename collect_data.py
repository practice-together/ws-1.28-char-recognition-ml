import serial
import json
import time
from pathlib import Path
import sys

class TouchDataCollector:
    def __init__(self, port, baud_rate=115200):
        """Initialize serial connection"""
        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            
            # Clear any existing data
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            # Wait for ESP32 to be ready
            time.sleep(2)
            
        except serial.SerialException as e:
            print(f"Failed to open {port}: {e}")
            raise
            
        self.samples_dir = Path("touch_samples")
        self.samples_dir.mkdir(exist_ok=True)
        
    def read_line(self):
        """Read a line and handle different line endings"""
        try:
            return self.ser.readline().decode('utf-8').strip()
        except UnicodeDecodeError:
            return ""
            
    def write_command(self, cmd):
        """Write a command and ensure it includes proper line ending"""
        try:
            full_cmd = f"{cmd}\r\n"
            self.ser.write(full_cmd.encode())
            self.ser.flush()
            time.sleep(0.1)  # Give ESP32 time to process
        except Exception as e:
            print(f"Failed to send command: {e}")
            raise
        
    def collect_letter_samples(self, letter, num_samples=10):
        """Collect multiple samples for a letter"""
        letter_samples = []
        letter_dir = self.samples_dir / letter
        letter_dir.mkdir(exist_ok=True)
        
        print(f"\nCollecting samples for letter {letter}")
        
        for i in range(num_samples):
            print(f"\nSample {i+1}/{num_samples}")
            print("Draw when ready...")
            
            # Send collection command and wait for acknowledgment
            command = f"COLLECT_{letter}"
            self.write_command(command)
            
            # Wait for acknowledgment with timeout
            timeout = time.time() + 5
            while time.time() < timeout:
                response = self.read_line()
                if response == f"COLLECTING_{letter}":
                    break
            else:
                print("Warning: No acknowledgment received")
            
            # Collect sample
            current_sample = []
            in_sample = False
            
            while True:
                line = self.read_line()
                
                if not line:
                    continue
                    
                if line == "START_SAMPLE":
                    in_sample = True
                    current_sample = []
                elif line == "END_SAMPLE":
                    break
                elif in_sample:
                    try:
                        point = json.loads(line)
                        current_sample.append(point)
                        print(".", end="", flush=True)  # Progress indicator
                    except json.JSONDecodeError:
                        print(f"\nInvalid data received: {line}")
            
            # Save individual sample
            if current_sample:
                sample_file = letter_dir / f"sample_{i+1}.json"
                with open(sample_file, 'w') as f:
                    json.dump(current_sample, f, indent=2)
                print(f"\nSaved {len(current_sample)} points")
            
            # Wait for ready signal with timeout
            timeout = time.time() + 5
            while time.time() < timeout:
                response = self.read_line()
                if response == "READY":
                    break
            else:
                print("Warning: No ready signal received")
            
            time.sleep(1)  # Brief pause between samples
    
    def collect_all_letters(self, samples_per_letter=10):
        """Collect samples for all letters"""
        letters = ['B', 'L', 'I', 'T', 'Z']
        
        print("Touch Data Collection")
        print("--------------------")
        print("Draw each letter when prompted.")
        print("You have 5 seconds to draw after the prompt.")
        
        for letter in letters:
            input(f"\nPress Enter to start collecting letter {letter}...")
            self.collect_letter_samples(letter, samples_per_letter)
        
        print("\nData collection complete!")
    
    def close(self):
        """Close serial connection"""
        try:
            self.write_command("EXIT")
            time.sleep(0.5)
            self.ser.close()
        except:
            pass

def main():
    if len(sys.argv) != 2:
        print("Usage: python collect_data.py <serial_port>")
        print("Example: python collect_data.py COM3  # on Windows")
        print("Example: python collect_data.py /dev/ttyACM0  # on Linux")
        sys.exit(1)
        
    port = sys.argv[1]
    
    try:
        collector = TouchDataCollector(port)
        collector.collect_all_letters()
    except serial.SerialException as e:
        print(f"Error: Could not open serial port {port}")
        print(f"Details: {e}")
    except KeyboardInterrupt:
        print("\nCollection interrupted by user")
    finally:
        try:
            collector.close()
        except:
            pass

if __name__ == "__main__":
    main()