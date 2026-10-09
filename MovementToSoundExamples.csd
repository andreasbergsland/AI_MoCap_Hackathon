<CsoundSynthesizer>
<CsOptions>
-odac -b128 -B256
</CsOptions>
<CsInstruments>
   
sr     = 48000
ksmps  = 32
nchnls = 2
0dbfs  = 1

;Initialize OSC session
giOSC OSCinit 9000

;Table containing MIDI note values
giNoteTable ftgen 0, 0, 0, -2, 53-12, 55-12, 60-12, 64-12, 53, 55, 60, 64, 53+12, 55+12, 60+12, 64+12, 53+24, 55+24, 60+24, 64+24 

;Global arrays for sending landmark data between instruments.
gkNose[] init 4
gkLeftEye[] init 4
gkRightEye[] init 4
gkLeftEar[] init 4
gkRightEar[] init 4

gkNoseVelocity[] init 4
gkLeftEyeVelocity[] init 4
gkRightEyeVelocity[] init 4
gkLeftEarVelocity[] init 4
gkRightEarVelocity[] init 4

gkLeftShoulder[] init 5
gkRightShoulder[] init 5
gkShoulderTilt init 0

gkLeftShoulderVelocity[] init 4
gkRightShoulderVelocity[] init 4

gkCenter[] init 3
gkCenterUpper[] init 3

gkLeftWrist[] init 5
gkRightWrist[] init 5
gkLeftElbow[] init 4
gkRightElbow[] init 4

gkLeftWristVelocity[] init 4
gkRightWristVelocity[] init 4
gkLeftElbowVelocity[] init 4
gkRightElbowVelocity[] init 4

gkLeftHip[] init 4
gkRightHip[] init 4

gkLeftHipVelocity[] init 4
gkRightHipVelocity[] init 4

gkLeftKnee[] init 4
gkRightKnee[] init 4
gkLeftAnkle[] init 4
gkRightAnkle[] init 4

gkLeftKneeVelocity[] init 4
gkRightKneeVelocity[] init 4
gkLeftAnkleVelocity[] init 4
gkRightAnkleVelocity[] init 4

;Use these macros below to easily get the movement data you want.
;HEAD
#define NOSE      # giOSC, "/pose/smooth/nose", "ffff" #      ;X, Y, Z, Presence
#define LEFT_EYE  # giOSC, "/pose/smooth/left_eye", "ffff" #  ;X, Y, Z, Presence
#define RIGHT_EYE # giOSC, "/pose/smooth/right_eye", "ffff" # ;X, Y, Z, Presence
#define LEFT_EAR  # giOSC, "/pose/smooth/left_ear", "ffff" #  ;X, Y, Z, Presence
#define RIGHT_EAR # giOSC, "/pose/smooth/right_ear", "ffff" # ;X, Y, Z, Presence

#define NOSE_VELOCITY      # giOSC, "/pose/raw/velocity/nose", "ffff" #      ;Speed X, Speed Y, Speed Z, Overall Speed
#define LEFT_EYE_VELOCITY  # giOSC, "/pose/raw/velocity/left_eye", "ffff" #  ;Speed X, Speed Y, Speed Z, Overall Speed
#define RIGHT_EYE_VELOCITY # giOSC, "/pose/raw/velocity/right_eye", "ffff" # ;Speed X, Speed Y, Speed Z, Overall Speed
#define LEFT_EAR_VELOCITY  # giOSC, "/pose/raw/velocity/left_ear", "ffff" #  ;Speed X, Speed Y, Speed Z, Overall Speed
#define RIGHT_EAR_VELOCITY # giOSC, "/pose/raw/velocity/right_ear", "ffff" # ;Speed X, Speed Y, Speed Z, Overall Speed

;SHOULDERS
#define LEFT_SHOULDER  # giOSC, "/pose/smooth/shoulder/left", "fffff" #  ;X, Y, Z, Presence, Reliability
#define RIGHT_SHOULDER # giOSC, "/pose/smooth/shoulder/right", "fffff" # ;X, Y, Z, Presence, Reliability
#define SHOULDER_TILT  # giOSC, "/pose/smooth/shoulder/tilt", "f" #      ;Tilt

#define LEFT_SHOULDER_VELOCITY  # giOSC, "/pose/raw/velocity/left_shoulder", "ffff" #  ;Speed X, Speed Y, Speed Z, Overall Speed
#define RIGHT_SHOULDER_VELOCITY # giOSC, "/pose/raw/velocity/right_shoulder", "ffff" # ;Speed X, Speed Y, Speed Z, Overall Speed

;CENTER
#define CENTER       # giOSC, "/pose/smooth/center", "fff" #       ;X, Y, Z
#define CENTER_UPPER # giOSC, "/pose/smooth/center/upper", "fff" # ;X, Y, Z

;ARMS
#define LEFT_WRIST  # giOSC, "/pose/smooth/wrist/left", "fffff" #  ;X, Y, Z, Presence, Reliability
#define RIGHT_WRIST # giOSC, "/pose/smooth/wrist/right", "fffff" # ;X, Y, Z, Presence, Reliability
#define LEFT_ELBOW  # giOSC, "/pose/smooth/left_elbow", "ffff" #   ;X, Y, Z, Presence
#define RIGHT_ELBOW # giOSC, "/pose/smooth/right_elbow", "ffff" #  ;X, Y, Z, Presence

#define LEFT_WRIST_VELOCITY  # giOSC, "/pose/raw/velocity/left_wrist", "ffff" #  ;Speed X, Speed Y, Speed Z, Overall Speed
#define RIGHT_WRIST_VELOCITY # giOSC, "/pose/raw/velocity/right_wrist", "ffff" # ;Speed X, Speed Y, Speed Z, Overall Speed
#define LEFT_ELBOW_VELOCITY  # giOSC, "/pose/raw/velocity/left_elbow", "ffff" #   ;Speed X, Speed Y, Speed Z, Overall Speed
#define RIGHT_ELBOW_VELOCITY # giOSC, "/pose/raw/velocity/right_elbow", "ffff" #  ;Speed X, Speed Y, Speed Z, Overall Speed

;HIPS
#define LEFT_HIP  # giOSC, "/pose/smooth/left_hip", "ffff" #   ;X, Y, Z, Presence
#define RIGHT_HIP # giOSC, "/pose/smooth/right_hip", "ffff" #  ;X, Y, Z, Presence

#define LEFT_HIP_VELOCITY  # giOSC, "/pose/raw/velocity/left_hip", "ffff" #  ;Speed X, Speed Y, Speed Z, Overall Speed
#define RIGHT_HIP_VELOCITY # giOSC, "/pose/raw/velocity/right_hip", "ffff" # ;Speed X, Speed Y, Speed Z, Overall Speed

;LEGS
#define LEFT_KNEE   # giOSC, "/pose/smooth/left_knee", "ffff" #   ;X, Y, Z, Presence
#define RIGHT_KNEE  # giOSC, "/pose/smooth/right_knee", "ffff" #  ;X, Y, Z, Presence
#define LEFT_ANKLE  # giOSC, "/pose/smooth/left_ankle", "ffff" #  ;X, Y, Z, Presence
#define RIGHT_ANKLE # giOSC, "/pose/smooth/right_ankle", "ffff" # ;X, Y, Z, Presence

#define LEFT_KNEE_VELOCITY   # giOSC, "/pose/raw/velocity/left_knee", "ffff" #   ;Speed X, Speed Y, Speed Z, Overall Speed
#define RIGHT_KNEE_VELOCITY  # giOSC, "/pose/raw/velocity/right_knee", "ffff" #  ;Speed X, Speed Y, Speed Z, Overall Speed
#define LEFT_ANKLE_VELOCITY  # giOSC, "/pose/raw/velocity/left_ankle", "ffff" #  ;Speed X, Speed Y, Speed Z, Overall Speed
#define RIGHT_ANKLE_VELOCITY # giOSC, "/pose/raw/velocity/right_ankle", "ffff" # ;Speed X, Speed Y, Speed Z, Overall Speed

instr InputOSC
    ;Get movement data via OSC. 
    ;Use one of listed macros to get the movement data you want.
    ;For sending data to other instruments, use global arrays.
    kLeftWrist, gkLeftWrist[] OSClisten $LEFT_WRIST
    kRightWrist, gkRightWrist[] OSClisten $RIGHT_WRIST
    kLeftWristVelocity, gkLeftWristVelocity[] OSClisten $LEFT_WRIST_VELOCITY
    kRightWristVelocity, gkRightWristVelocity[] OSClisten $RIGHT_WRIST_VELOCITY
endin

instr DistanceBetweenArms
    kLx = gkLeftWrist[0]
    kLy = gkLeftWrist[1]
    kRx = gkRightWrist[0]
    kRy = gkRightWrist[1]

    ;Calculate distance between two points.
    kDistance = sqrt((kLx-kRx)^2 + (kLy-kRy)^2)

    ;Change this value to run different examples.
    iFunction = 1

    if iFunction == 1 then ;EXAMPLE 1 - Distance controls note range.

        ;Generate new notes 8 times per second.
        iRate = 8
        kNoteTrig metro iRate

        ;Generate random number between 0 and 1, centered around 0.5 and scaled by distance.
        ;Used as an index for grabbing note values from the function table.
        ki rand 0.5
        ki = (ki * kDistance) + 0.5
        ki limit ki, 0, 0.99
        
        if kNoteTrig == 1 then
            kNote tab ki, giNoteTable, 1
            event "i", "OutputSine", 0, 1.0/iRate, kNote
        endif

    elseif iFunction == 2 then ;EXAMPLE 2 - Distance controls note rate.

        ;Scales the distance value to correspond to a range of rates.
        ;The distance value is inverted so that shorter distance leads to higher rate.
        kRate scale 1-kDistance, 15, 2
        kNoteTrig metro kRate

        ;Generate a random value between 0 and 1 to use as an index for grabbing note values from the function table.
        ki rand 0.5
        ki += 0.5
        ki limit ki, 0, 0.99
        
        if kNoteTrig == 1 then
            kNote tab ki, giNoteTable, 1
            event "i", "OutputSine", 0, 1.0/kRate, kNote
        endif
    endif

endin

instr VelocityTrigger
    kLx = gkLeftWristVelocity[0]
    kLy = gkLeftWristVelocity[1]
    kLv = gkLeftWristVelocity[3]
    kRx = gkRightWristVelocity[0]
    kRy = gkRightWristVelocity[1]
    kRv = gkRightWristVelocity[3]

    ;Smoothing to remove jitter and false triggers.
    iSmoothing = 0.1
    kLvs port kLv, iSmoothing
    kRvs port kRv, iSmoothing

    ;Set the threshold for how fast you must move before triggering.
    iThreshold = 0.6
    ;Set the minimum time between each trigger.
    iPause = 0.1
    ;Set the maximum velocity before the amplitude is max.
    iAmpLimit = 2

    kTrigL = trigger(trighold(trigger(kLvs, iThreshold, 0), iPause), 0.5, 0)
    kTrigR = trigger(trighold(trigger(kRvs, iThreshold, 0), iPause), 0.5, 0)

    ;Delay the trigger so that it is closer to peak velocity.
    iDelay = .035
    kDelayTrigL delayk kTrigL, iDelay
    kDelayTrigR delayk kTrigR, iDelay

    if kDelayTrigL == 1 then
        kAmp scale limit(kLvs, iThreshold, iAmpLimit), 1, 0, iAmpLimit, iThreshold
        event "i", "OutputNoise", 0, 0.5, kAmp, 0
    endif

    if kDelayTrigR == 1 then
        kAmp scale limit(kRvs, iThreshold, iAmpLimit), 1, 0, iAmpLimit, iThreshold
        event "i", "OutputNoise", 0, 0.5, kAmp, 1
    endif

endin

instr PositionalTrigger
    ;By having several instances of this instrument, we can set up multiple positional triggers.
    iX    = p4
    iY    = p5
    iSize = p6 ;How large the trigger zone should be.
    iFreq = p7 ;Center frequency for bandpass filter.

    kLx = gkLeftWrist[0]
    kLy = gkLeftWrist[1]
    kRx = gkRightWrist[0]
    kRy = gkRightWrist[1]

    ;Calculate distance between two points.
    kDistanceL = sqrt((kLx-iX)^2 + (kLy-iY)^2)
    kDistanceR = sqrt((kRx-iX)^2 + (kRy-iY)^2)

    ;Always gives you the distance of the nearest landmark.
    kNearest min kDistanceL, kDistanceR

    ;Change this value to run different examples.
    iFunction = 1

    if iFunction == 1 then ;EXAMPLE 1 - Trigger when near defined point.

        ;Set the minimum time between each trigger.
        iPause = 0.1 

        kTrig = trigger(trighold(trigger(kNearest, iSize, 1), iPause), 0.5, 1)
        if kTrig == 1 then
            event "i", "OutputNoise", 0, 0.5, 1, 0.5
        endif

    elseif iFunction == 2 then ;EXAMPLE 2 - Fade in when near defined point.

        ;Only fade from 0% to 100% once inside the defined radius.
        kAmp scale limit(kNearest, 0, iSize), 1, 0, iSize, 0
        kAmp = 1 - kAmp

        aNoise rand 0.5*kAmp
        aFilter butterbp aNoise, iFreq, iFreq*0.1

        out aFilter

    endif

endin

instr GetCurrentPosition
    kKey, kPress sensekey

    ;Change these if you want the position of a different landmark.
    kX = gkLeftWrist[0]
    kY = gkLeftWrist[1]

    ;Prints the current position when SPACEBAR is pressed.  
    if kKey == 32 && trigger(kPress, 0.5, 0) == 1 then
        printsk "X: %f  Y: %f\n", kX, kY
    endif
endin

instr OutputMIDI
    iDur = p3
    iNote = p4

    noteondur 1, iNote, 64, iDur
endin

instr OutputSine
    iDur = p3
    iNote = p4

    iCps mtof iNote
    aDecay line 0.5, iDur, 0.0

    aSine oscil 0.5, iCps

    out aSine*aDecay
endin

instr OutputNoise
    iDur = p3
    iAmp = p4
    iPan = p5

    aDecay line 0.5, iDur, 0.0
    aNoise rand 0.5 * iAmp
    aL, aR pan2 aNoise, iPan

    outs aL*aDecay, aR*aDecay
endin

</CsInstruments>
<CsScore>
i"InputOSC" 0 z
i"GetCurrentPosition" 0 z

;i"DistanceBetweenArms" 0 z
;i"VelocityTrigger" 0 z

i"PositionalTrigger" 0 z 0.2 0.2 0.2 5000
i"PositionalTrigger" 0 z 0.8 0.2 0.2 7000
i"PositionalTrigger" 0 z 0.2 0.8 0.2 2000
i"PositionalTrigger" 0 z 0.8 0.8 0.2 500
</CsScore>
</CsoundSynthesizer>