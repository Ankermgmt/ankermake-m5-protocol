; Test Cube 5x5x5mm for Print Control Testing
; Generated for AnkerMake M5
; Total print time: ~2 minutes

; Startup (PETG settings: 250°C nozzle, 80°C bed)
M140 S80 ; Set bed temp
M104 S250 ; Set hotend temp
M190 S80 ; Wait for bed
M109 S250 ; Wait for hotend
G28 ; Home all axes
G29 ; Auto bed leveling
G92 E0 ; Reset extruder
G1 Z2.0 F3000 ; Move Z up
G1 X10 Y10 F5000 ; Move to start
G1 Z0.2 F3000 ; Lower nozzle

; Layer 1 (0.2mm)
G1 E2 F1500 ; Prime
G1 X15 Y10 E2.5 F1000
G1 X15 Y15 E3.0
G1 X10 Y15 E3.5
G1 X10 Y10 E4.0
G1 Z0.4 F3000

; Layer 2 (0.4mm)
G1 X15 Y10 E4.5 F1000
G1 X15 Y15 E5.0
G1 X10 Y15 E5.5
G1 X10 Y10 E6.0
G1 Z0.6 F3000

; Layer 3 (0.6mm)
G1 X15 Y10 E6.5 F1000
G1 X15 Y15 E7.0
G1 X10 Y15 E7.5
G1 X10 Y10 E8.0
G1 Z0.8 F3000

; Layer 4 (0.8mm)
G1 X15 Y10 E8.5 F1000
G1 X15 Y15 E9.0
G1 X10 Y15 E9.5
G1 X10 Y10 E10.0
G1 Z1.0 F3000

; Layer 5 (1.0mm)
G1 X15 Y10 E10.5 F1000
G1 X15 Y15 E11.0
G1 X10 Y15 E11.5
G1 X10 Y10 E12.0
G1 Z1.2 F3000

; Layer 6 (1.2mm)
G1 X15 Y10 E12.5 F1000
G1 X15 Y15 E13.0
G1 X10 Y15 E13.5
G1 X10 Y10 E14.0
G1 Z1.4 F3000

; Layer 7 (1.4mm)
G1 X15 Y10 E14.5 F1000
G1 X15 Y15 E15.0
G1 X10 Y15 E15.5
G1 X10 Y10 E16.0
G1 Z1.6 F3000

; Layer 8 (1.6mm)
G1 X15 Y10 E16.5 F1000
G1 X15 Y15 E17.0
G1 X10 Y15 E17.5
G1 X10 Y10 E18.0
G1 Z1.8 F3000

; Layer 9 (1.8mm)
G1 X15 Y10 E18.5 F1000
G1 X15 Y15 E19.0
G1 X10 Y15 E19.5
G1 X10 Y10 E20.0
G1 Z2.0 F3000

; Layer 10 (2.0mm)
G1 X15 Y10 E20.5 F1000
G1 X15 Y15 E21.0
G1 X10 Y15 E21.5
G1 X10 Y10 E22.0

; Finish
G1 E20 F1500 ; Retract
G1 Z10 F3000 ; Raise nozzle
G28 X Y ; Home X Y
M104 S0 ; Turn off hotend
M140 S0 ; Turn off bed
M106 S0 ; Turn off fan
M84 ; Disable motors
; Test print complete
