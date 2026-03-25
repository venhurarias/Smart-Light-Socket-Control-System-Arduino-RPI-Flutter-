#include <Bounce2.h>

#define LIGHT_BTN 9
#define EXT_BTN 10

#define LIGHT_SSR 11
#define EXT_SSR 12
int mode = 0;

Bounce debouncerL = Bounce();
Bounce debouncerE = Bounce();

void setup() {
  Serial.begin(9600);
  Serial.setTimeout(100);
  pinMode(LIGHT_BTN, INPUT_PULLUP);
  pinMode(EXT_BTN, INPUT_PULLUP);
  debouncerL.attach(LIGHT_BTN);
  debouncerL.interval(100);
  debouncerE.attach(EXT_BTN);
  debouncerE.interval(100);

  pinMode(LIGHT_SSR, OUTPUT);
  pinMode(EXT_SSR, OUTPUT);
}

void loop() {
  switch (mode) {
    case 0:
      if (isLightPressed()) {
        Serial.print("l");
        mode = 1;
      } else if (isExtPressed()) {
        Serial.print("e");
        mode = 1;
      }
      break;
    case 1:
      if (!isLightPressed() && !isExtPressed()) {
        mode = 0;
      }
      break;
  }

  if (Serial.available()) {
    String s = Serial.readString();
    s.trim();
    if (s == "0") {
      LightOff();
      ExtOff();
    } else if (s == "1") {
      LightOn();
      ExtOff();
    } else if (s == "2") {
      LightOff();
      ExtOn();
    } else if (s == "3") {
      LightOn();
      ExtOn();
    }
  }
}

bool isExtPressed() {
  debouncerE.update();
  return debouncerE.fell();
}

bool isLightPressed() {
  debouncerL.update();
  return debouncerL.fell();
}


void LightOn() {
  digitalWrite(LIGHT_SSR, HIGH);
}

void LightOff() {
  digitalWrite(LIGHT_SSR, LOW);
}


void ExtOn() {
  digitalWrite(EXT_SSR, HIGH);
}

void ExtOff() {
  digitalWrite(EXT_SSR, LOW);
}
