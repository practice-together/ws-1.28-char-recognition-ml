import cst816
from machine import Pin, SPI
import gc9a01
import time
import json
import gc
from bitmap import vga1_bold_16x32 as font

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class TouchCollector:
    def __init__(self):
        print("Initializing TouchCollector...")
        
        # Initialize SPI
        print("Initializing SPI...")
        spi = SPI(2, baudrate=80000000, polarity=0, sck=Pin(10), mosi=Pin(11))
        print("SPI initialized")
        
        # Initialize display
        print("Initializing display...")
        self.tft = gc9a01.GC9A01(
            spi,
            240,
            240,
            reset=Pin(14, Pin.OUT),
            cs=Pin(9, Pin.OUT),
            dc=Pin(8, Pin.OUT),
            backlight=Pin(2, Pin.OUT),
            rotation=0)
        print("Display driver initialized")
        
        # Initialize touch
        print("Initializing touch sensor...")
        self.touch = cst816.CST816()
        print("Touch sensor initialized")
        
        # Initialize display hardware
        print("Initializing display hardware...")
        self.tft.init()
        print("Display hardware initialized")
        
        # Define colors
        print("Setting up colors...")
        self.DARK_BLUE = gc9a01.color565(16, 24, 45)
        self.CORAL = gc9a01.color565(255, 127, 108)
        self.MINT = gc9a01.color565(108, 255, 184)
        self.LAVENDER = gc9a01.color565(186, 178, 255)
        self.WHITE = gc9a01.color565(255, 255, 255)
        print("Colors defined")
        
        # Show welcome message
        self.show_welcome()
        
        # Initialize points list
        self.points = []
    
    def show_welcome(self):
        """Show welcome message"""
        self.tft.fill(self.DARK_BLUE)
        self.center_text("Ready", 100, self.MINT)
        self.center_text("for", 130, self.MINT)
        self.center_text("samples!", 160, self.MINT)
    
    def center_text(self, text, y, color):
        """Center text on screen at given y position"""
        x = (240 - len(text) * font.WIDTH) // 2
        self.tft.text(font, text, x, y, color, self.DARK_BLUE)
            
    def draw_point(self, x, y):
        """Draw a single point"""
        self.tft.pixel(x, y, self.CORAL)
        # Make point more visible
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                new_x = x + dx
                new_y = y + dy
                if 0 <= new_x < 240 and 0 <= new_y < 240:
                    self.tft.pixel(new_x, new_y, self.CORAL)
    
    def draw_line(self, x1, y1, x2, y2):
        """Draw a line between two points"""
        self.tft.line(x1, y1, x2, y2, self.CORAL)
        
    def collect_letter(self, letter):
        print(f"Starting collection for letter {letter}")
        self.points = []
        
        # Clear screen and show instructions
        self.tft.fill(self.DARK_BLUE)
        
        # Draw the target letter
        x = (240 - font.WIDTH) // 2
        self.tft.text(font, letter, x, 10, self.WHITE, self.DARK_BLUE)
        
        # Show instruction
        self.center_text("Draw Above", 200, self.LAVENDER)
        
        print("START_SAMPLE")
        start_time = time.time()
        last_point = None
        
        # Continue for full 5 seconds regardless of finger lift
        while time.time() - start_time < 5:
            try:
                point = self.touch.get_point()
                pressed = self.touch.get_touch()
                
                if pressed:
                    new_point = Point(point.x_point, point.y_point)
                    self.points.append(new_point)
                    
                    # Draw the point or line
                    if last_point:
                        self.draw_line(
                            last_point.x,
                            last_point.y,
                            new_point.x,
                            new_point.y
                        )
                    else:
                        self.draw_point(point.x_point, point.y_point)
                    
                    last_point = new_point
                    
                    # Log the point data
                    point_data = {
                        "x": point.x_point,
                        "y": point.y_point,
                        "time": time.time() - start_time
                    }
                    print(json.dumps(point_data))
                else:
                    # Reset last_point when finger is lifted
                    last_point = None
                    
            except Exception as e:
                print(f"Error in touch reading: {e}")
                continue
                
            time.sleep(0.01)
        
        # Show completion message
        self.tft.fill(self.DARK_BLUE)
        self.center_text("Sample", 100, self.MINT)
        self.center_text("Saved!", 130, self.MINT)
        
        print("END_SAMPLE")
        time.sleep(1)
        
        # Show ready message
        self.show_welcome()
        
    def run(self):
        print("Starting main loop")
        self.show_welcome()
        
        while True:
            try:
                print("Waiting for command...")
                cmd = input().strip()
                print(f"Received command: {cmd}")
                
                if cmd.startswith("COLLECT"):
                    letter = cmd.split("_")[1]
                    print(f"COLLECTING_{letter}")
                    self.collect_letter(letter)
                    print("READY")
                
                elif cmd == "EXIT":
                    print("Exiting...")
                    self.tft.fill(self.DARK_BLUE)
                    self.center_text("Goodbye!", 110, self.LAVENDER)
                    time.sleep(1)
                    break
                    
            except Exception as e:
                print(f"Error in main loop: {e}")
                self.tft.fill(self.DARK_BLUE)
                self.center_text("Error!", 110, self.CORAL)
                continue

def main():
    print("Starting program")
    gc.enable()
    gc.collect()
    
    try:
        collector = TouchCollector()
        collector.run()
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        print("Program ended")

if __name__ == "__main__":
    main()