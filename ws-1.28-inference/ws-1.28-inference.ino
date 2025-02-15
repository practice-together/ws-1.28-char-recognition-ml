#include <Arduino.h>
#include <MicroTFLite.h>
#include "LCD_Test.h"
#include "model.h"

// define some colors (16-bit RGB565 format)
#define BG_COLOR 0x1B2A // Dark blue background (11,17,42)
#define TEXT_COLOR 0xFFFF // White text
#define ACCENT_COLOR 0x867F // Coral for drawing (255,127,108)
#define SUCCESS_COLOR 0x5ED5 // Mint green (108,255,184)

// ML model parameters 
constexpr int tensorArenaSize = 100 * 1024;
alignas(16) byte tensorArena[tensorArenaSize];
const int imageSize = 32;
const int imagePixels = imageSize * imageSize;
const float scaleFactor = 31.0f / 240.0f;
const char* CLASSES[] = {"B", "L", "I", "T", "Z"};

// Hardware objects
CST816S touch(6, 7, 13, 5);  // sda, scl, rst, irq
UWORD Imagesize = LCD_1IN28_HEIGHT * LCD_1IN28_WIDTH * 2;
UWORD *BlackImage;
float testImage[imagePixels];

// Helper function to center text
void drawCenteredText(int y, const char* text, sFONT* font, UWORD textColor, UWORD bgColor) {
    int textWidth = strlen(text) * font->Width;
    int x = (LCD_1IN28_WIDTH - textWidth) / 2;
    Paint_DrawString_EN(x, y, text, font, textColor, bgColor);
}

void clearImage(float* image) {
    memset(image, 0, imagePixels * sizeof(float));
}

void drawPixel(float* image, int x, int y) {
    if (x >= 0 && x < imageSize && y >= 0 && y < imageSize) {
        image[y * imageSize + x] = 1.0f;
    }
}

bool captureTouchInput(float* image) {
    Paint_Clear(BG_COLOR);
    drawCenteredText(20, "Drawing Mode", &Font20, TEXT_COLOR, BG_COLOR);
    LCD_1IN28_Display(BlackImage);
    
    clearImage(image);
    bool hasDrawing = false;
    bool touchDetected = false;
    unsigned long startTime = 0;
    
    // Wait for initial touch
    while (!touchDetected) {
        if (touch.available()) {
            touchDetected = true;
            startTime = millis();
            break;
        }
        delay(10);
    }
    
    // If touch detected, start 5-second drawing period
    while (touchDetected && (millis() - startTime < 5000)) {
        if (touch.available()) {
            hasDrawing = true;
            Paint_DrawPoint(touch.data.x, touch.data.y, ACCENT_COLOR, DOT_PIXEL_3X3, DOT_FILL_RIGHTUP);
            LCD_1IN28_DisplayWindows(touch.data.x, touch.data.y, touch.data.x + 3, touch.data.y + 3, BlackImage);
            
            int scaled_x = round(touch.data.x * scaleFactor);
            int scaled_y = round(touch.data.y * scaleFactor);
            drawPixel(image, scaled_x, scaled_y);
        }
    }
    
    // Show completion message
    if (hasDrawing) {
        Paint_Clear(BG_COLOR);
        drawCenteredText(100, "Processing...", &Font20, SUCCESS_COLOR, BG_COLOR);
        LCD_1IN28_Display(BlackImage);
        delay(200);
    }
    
    return hasDrawing;
}

void displayPrediction(const char* prediction) {
    Paint_Clear(BG_COLOR);
    
    // Draw prediction
    drawCenteredText(80, "Predicted:", &Font20, TEXT_COLOR, BG_COLOR);
    drawCenteredText(120, prediction, &Font24, SUCCESS_COLOR, BG_COLOR);
    
    LCD_1IN28_Display(BlackImage);
    delay(2000);
}

void runInference(float* testImage) {
    for (int i = 0; i < imagePixels; i++) {
        ModelSetInput(testImage[i], i);
    }
    
    if (!ModelRunInference()) {
        return;
    }
    
    float probs[5];
    for (int i = 0; i < 5; i++) {
        probs[i] = ModelGetOutput(i);
    }
    
    int predictedIndex = std::max_element(probs, probs + 5) - probs;
    displayPrediction(CLASSES[predictedIndex]);
}

void setup() {
    Serial.begin(115200);
    touch.begin();
    
    // PSRAM Initialize
    if(psramInit()){
        Serial.println("\nPSRAM is correctly initialized");
    } else {
        Serial.println("PSRAM not available");
    }
    
    if ((BlackImage = (UWORD *)ps_malloc(Imagesize)) == NULL) {
        Serial.println("Failed to apply for black memory...");
        exit(0);
    }
    
    // Hardware init
    if (DEV_Module_Init() != 0) {
        Serial.println("GPIO Init Fail!");
    } else {
        Serial.println("GPIO Init successful!");
        
        // Initialize display
        LCD_1IN28_Init(HORIZONTAL);
        LCD_1IN28_Clear(BG_COLOR);  
        
        // Create new image cache
        Paint_NewImage((UBYTE *)BlackImage, LCD_1IN28.WIDTH, LCD_1IN28.HEIGHT, 0, BG_COLOR);
        Paint_SetScale(65);
        Paint_SetRotate(ROTATE_0);
        Paint_Clear(BG_COLOR);
        
        // Initialize model
        if (!ModelInit(model, tensorArena, tensorArenaSize)) {
            Serial.println("Model initialization failed!");
            while (true) { ; }
        }
        
        // Initial display
        Paint_Clear(BG_COLOR);
        drawCenteredText(100, "Ready!", &Font24, SUCCESS_COLOR, BG_COLOR);
        LCD_1IN28_Display(BlackImage);
        delay(1000);
    }
}

void loop() {
    if (captureTouchInput(testImage)) {
        runInference(testImage);
    }
    delay(100);
}