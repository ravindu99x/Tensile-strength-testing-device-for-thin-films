#include "HX711.h"
#include "AccelStepper.h"

//LCD Display
#include <Adafruit_GFX.h>    // Core graphics library
#include <Adafruit_ST7735.h> // Hardware-specific library
#include <SPI.h>

#define TFT_CS     9
#define TFT_RST    7 
#define TFT_DC     8

Adafruit_ST7735 tft = Adafruit_ST7735(TFT_CS,  TFT_DC, TFT_RST);
#define TFT_SCLK 13   
#define TFT_MOSI 11   

float p = 3.1415926;

// Load cell settings
#define calibration_factor 394
#define LOADCELL_DOUT_PIN  3
#define LOADCELL_SCK_PIN  2
HX711 scale;

// Stepper motor settings
#define dirPin 4
#define stepPin 5
#define motorInterfaceType 1
double step_length = 0.008/6000;
float sample_length = 0.11;
float sample_width = 0.011;
AccelStepper stepper = AccelStepper(motorInterfaceType, stepPin, dirPin);

//LED Indicators
#define Standby_LED 10
#define running_LED 12
long count= 0;
bool testRunning = false;

// Add global variables for motor speed and sample thickness
int motorSpeed = 1000; // Default speed
double sampleThickness = 0.1; // Default thickness in mm

void setup() {
  //LCD Display
  tft.initR(INITR_BLACKTAB);   // initialize a ST7735S chip, black tab
  tft.fillScreen(ST7735_RED);
  testdrawtext(5, 25, "EPL Mini Project", ST7735_WHITE);
  testdrawtext(5, 35, "Tensile Testing", ST7735_WHITE);
  testdrawtext(5, 45, "s14832", ST7735_WHITE);
  delay(2000);
  tft.fillScreen(ST7735_BLUE);
  tft.setTextSize(1.5);
  testdrawtext(5, 55, "Processing...", ST7735_WHITE);
  delay(2000);
  tft.fillScreen(ST7735_WHITE);
  testdrawtext(5, 55, "Press Start...", ST7735_BLACK);
  delay(2000);
  
  pinMode(Standby_LED, OUTPUT);
  pinMode(running_LED, OUTPUT);
  
  Serial.begin(115200);
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(calibration_factor);
  scale.tare();
  
  stepper.setCurrentPosition(0);
  stepper.setMaxSpeed(8000);
  stepper.setSpeed(0);
  digitalWrite(Standby_LED, HIGH);
}

void loop() {

  // Check for new commands
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    if (command.startsWith("START")) {
      // Split the command by commas
      int firstCommaIndex = command.indexOf(',');
      int secondCommaIndex = command.indexOf(',', firstCommaIndex + 1);

      String speedStr = command.substring(firstCommaIndex + 1, secondCommaIndex);
      String thicknessStr = command.substring(secondCommaIndex + 1);

      // Convert speed and thickness to integers
      motorSpeed = speedStr.toInt();
      sampleThickness = thicknessStr.toFloat();

      testRunning = true;
      tft.fillScreen(ST7735_GREEN);
      
      testdrawtext(5, 25, "EPL Mini Project", ST7735_BLACK);
      testdrawtext(5, 35, "Tensile Testing", ST7735_BLACK);
      testdrawtext(5, 45, "s14832", ST7735_BLACK);
      testdrawtext(5, 75, "RUNNING...", ST7735_BLACK);
      testdrawtext(5, 85, "Collecting data...", ST7735_BLACK);
      testdrawtext(5, 95, "This may take a while...", ST7735_BLACK);
//      stepper.setSpeed(8000);
//      stepper.run();
      digitalWrite(Standby_LED, LOW);
      digitalWrite(running_LED, HIGH);

      
    } else if (command == "RESET") {
      testRunning = false;
      tft.fillScreen(ST7735_YELLOW);
      testdrawtext(5, 25, "EPL Mini Project", ST7735_BLACK);
      testdrawtext(5, 35, "Tensile Testing", ST7735_BLACK);
      testdrawtext(5, 45, "s14832", ST7735_BLACK);
      
      testdrawtext(5, 65, "DEVICE RESETTING...", ST7735_BLACK);
      testdrawtext(5, 75, "Please save files before closing the window...", ST7735_BLACK);
      testdrawtext(5, 115, "DEVICE READY...", ST7735_BLACK);
      stepper.moveTo(0);
      count = 0;
//      stepper.setSpeed(8000); // Adjust as needed
//      stepper.run();
      digitalWrite(running_LED, LOW);
      digitalWrite(Standby_LED, HIGH);
    }
  }

  // Run test if started
  if (testRunning) {
    stepper.setSpeed(-3300);
    if (stepper.distanceToGo() == 0) {
      // Example: move back and forth
      long newPos = (stepper.currentPosition() == 0) ? 6400 : 0;
      stepper.moveTo(newPos);
    }
    count = stepper.currentPosition();
    // Collect and send data
    double sensorValue1 = (step_length * count) / sample_length; // Adjust sample_length as needed
//    double sensorValue1 =  count; // Adjust sample_length as needed
    double area = sample_width*sampleThickness;
    double sensorValue2 = (scale.get_units()/(1000*area))*9.81;
//    double sensorValue2 = (scale.get_units()/1000)*10;
    if (sensorValue2 > -1) {
//      stepper.setSpeed(8000);
//      stepper.run();
      Serial.print(abs(sensorValue1), 7);
      Serial.print(", ");
      Serial.println(sensorValue2, 2);
//      delay(10);
    }
    stepper.run();
  } else if (stepper.distanceToGo() != 0) {
    // Continue moving to the reset position if not there yet
    stepper.setSpeed(3300); // Adjust as needed
    stepper.run();
  }
  
  delay(10); // Small delay to stabilize loop, adjust as needed
}

void testdrawtext(int wid, int hei, char *text, uint16_t color) {
  tft.setCursor(wid, hei);
  tft.setTextColor(color);
  tft.setTextWrap(true);
  tft.print(text);
}

//void testdrawScreenData(){
//  tft.setCursor(0,20);
//  tft.println("Screen Data:");
//  tft.print("Screen Width: ");
//  tft.println(tft.width());
//  tft.print("Screen Height: ");
//  tft.println(tft.height());
//}
