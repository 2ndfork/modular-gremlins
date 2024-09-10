import random

root = ["C","Db","D","Eb","E","F","F#","G","Ab","A","Bb","B"]

foldedKeys = ["C","Db","D","Eb","E","F","F#","G","Ab","A","Bb","B",
              "C","C#","D","D#","E","F","Gb","G","G#","A","A#","B"]

quality = ["","m","7","m7","9","m9","11","m11","13","m13",
           "Maj7","m(Maj7)","Maj9","m(Maj9)","Maj13","m(Maj13)","6","m6","69","m69",
           "dim7", "min7(b5)",
           "+", "+7","sus","7(b9)","7(#9)","7(b5)"]          
flatKeys = ["F", "Bb", "Eb", "Ab", "Db", "Gb", "Cb"]
threeOctaveFlat = ["C","Db","D","Eb","E","F","Gb","G","Ab","A","Bb","B","C","Db","D","Eb","E","F","Gb","G","Ab","A","Bb","B","C","Db","D","Eb","E","F","Gb","G","Ab","A","Bb","B"]
threeOctaveSharp = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B","C","C#","D","D#","E","F","F#","G","G#","A","A#","B","C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]
romanAccidentals = ["#", "b"]
romanNoteDigits = ["I", "i", "V", "v"]

romanMajorScale    = ["I", "II", "III", "IV", "V", "VI", "VII"]
romanMinorScale    = ["i", "ii", "iii", "iv", "v", "vi", "vii"]
naturalScale  = ["C", "D",  "E",   "F",  "G", "A",  "B"]

# ==============================================================================
#  Helper functions for chord inversion

def invert(chord):
    """Invert a given chord one time."""
    return chord[1:] + [chord[0]]


def inversion(chord, numTimes) :
  if numTimes > 0 :
    for i in range(0, numTimes):
      chord = invert(chord)
  return chord  

def getEnharmonicScale(chordRoot, key) :
  if key in flatKeys or (chordRoot not in threeOctaveSharp):
    return threeOctaveFlat
  return threeOctaveSharp  

def voiceMe(chordRoot, otherIntervals = [], chordInversion = 0, isRootless = False, key = "C"):
  threeOctave = []
  buf = []
  threeOctave = getEnharmonicScale(chordRoot, key)
  index = threeOctave.index(chordRoot)
  if not isRootless :
    buf.append(threeOctave[index])
  
  for x in otherIntervals: 
    buf.append(threeOctave[index + x])
  return inversion(buf, chordInversion)


# An internal helper function to convert double sharps, flats etc.
# to their normal enharmonic equivalent
def convertEnharmonic(chordRoot, key) :
  if len(chordRoot) > 1:
    shortIndex = 0
    threeOctave = []
    threeOctave = getEnharmonicScale(chordRoot, key)
    shortIndex = threeOctave.index(chordRoot[0:1])

    for x in range(1, len(chordRoot)) :
      if chordRoot[x] == "b" :
        threeOctave = threeOctaveFlat
        shortIndex = shortIndex - 1
        if shortIndex < 0 :
          shortIndex = shortIndex + 12
      elif chordRoot[x] == "#" :
        threeOctave = threeOctaveSharp
        shortIndex = shortIndex + 1     
    return threeOctave[shortIndex]
  else :
    return chordRoot  


# An internal helper function to create simple text charts when it is given to one of
# the deck functions below.
def SimpleTextChart(cardFunc):
  slashes = "/ / / /     "
  for i in range(0,8):
    line = "\n"
    rhythm = ""
    for i in range(0,4):
      value = cardFunc()
      line += value.ljust(12, " ")
      rhythm += slashes
    print(line)
    print(rhythm + "\n") 

def rawChart(cardFunc) :
  retval = []
  for i in range(0,32):
    retval.append(cardFunc())
  return retval  
  
def processSlashBass(chordTop, chordBottom) :
  if(chordBottom == "") :
    return chordTop

  bassNoteIndex = foldedKeys.index(chordBottom) % 12
  iCount = -1 
  for x in chordTop :
    iCount = iCount + 1
    if (foldedKeys.index(x) % 12) == bassNoteIndex :
      return inversion(chordTop, iCount)
  # If we get here, it is because the chordBottom was missing
  chordTop.insert(0,chordBottom)
  return chordTop     

# An internal helper function to show the voicing of a single chord for
# training purposes
def SimpleTextVoicing(description, qualityIndex, voicingFunc):
  print("\n" + description + "\n")
  for i in range(0,11):
    rootName = root[i]
    cup = voicingFunc(rootName)
    cupString = " ".join(cup)
    print(rootName + quality[qualityIndex] + "\t(" + cupString + ")")
  print("")


def cup(shorthand, key ="C"):
   print(realize(shorthand, key, cup=True))
   print("\n")

def triad(shorthand, key ="C"):
   print(realize(shorthand, key, cup=False))
   print("\n")   


# A main function for parsing a progression of chords using
# their short common name EX: C9, Gmaj7
def realize(shorthand, key = "C", cup = False):

  threeOctave = []
  chordFunc = major # default
  chordInversion = 0
  doCup = cup
  funcIndex = 0
  functionSelector = qualityFunc
  qualityOffset = 0
  noRoot = False
  romanAccidental = ""
  romanMinor = False
  romanMajor = False
  rootIndex = 0
  remaining  = shorthand
  slashBass = ""

  # split it to allow chords separated by spaces
  if " " in shorthand:
    shorthand = shorthand.split()
  
  # if this a progression, then call it recursively
  if isinstance(shorthand, list):
        res = []
        for x in shorthand:
            res.append(realize(x, key, cup))
        return res
  

  # Handle polychords separated by a semicolon
  # Call in recursively only this time concat the two parts
  # as individual elements rather than as an array
  if ";" in shorthand:
    shorthand = shorthand.split(";")
    if isinstance(shorthand, list):
        res = []
        for x in shorthand:
            poly = realize(x, key, cup)
            for y in poly :
              res.append(y)
        return res

  # Begin the process of handling slash Bass Notes
  if "/" in shorthand :
    shorthand = shorthand.split("/")
    if isinstance(shorthand, list):
        slashBass = shorthand[1]
        shorthand = shorthand[0]


  # If any accidentals comes first, then deal with it.
  for x in range(0,len(shorthand)) : 
    if shorthand[rootIndex] in romanAccidentals :
      romanAccidental = romanAccidental + shorthand[rootIndex]
      rootIndex = rootIndex + 1
      qualityOffset = qualityOffset + 1
    else :
      break  


  # If roman Numerals don't process yet
  if shorthand[rootIndex] in romanNoteDigits:
    rootName = ""
    remaining = shorthand[rootIndex:]
  else:
    # else move on past the note Name
    rootName = shorthand[rootIndex]
    qualityOffset = qualityOffset + 1;
    remaining = shorthand[(rootIndex + 1):]
  
  for n in remaining:
      if n == "#":
          rootName += n
      elif n == "b":
          if romanMajor or romanMinor :
            chordInversion = 1
          else :  
            rootName += n
      elif n == "c":
          if romanMajor or romanMinor :
            chordInversion = 2     
      elif n == "^":
          doCup = True  
      elif n == "_":
          noRoot = True   
      elif n == "I":
          rootName += n
          romanMajor = True
      elif n == "i":
          rootName += n
          romanMinor = True
      elif n == "V":
          rootName += n
          romanMajor = True
      elif n == "v":
          rootName += n
          romanMinor = True                        
      else:
          break
      qualityOffset = qualityOffset + 1  
 
  # Do this now, as romanMinor may need it
  chordQuality = shorthand[qualityOffset:] 
  
  # Deal with any romans now
  if romanMajor:     
    naturalRoot= naturalScale[romanMajorScale.index(rootName)]
    naturalIndex = root.index(naturalRoot)
    naturalIndex = naturalIndex + (foldedKeys.index(key) % 12)
    threeOctave = getEnharmonicScale(naturalRoot, key)
    rootName = threeOctave[naturalIndex] + romanAccidental

  if romanMinor:     
    naturalRoot= naturalScale[romanMinorScale.index(rootName)]
    naturalIndex = root.index(naturalRoot)
    naturalIndex = naturalIndex + (foldedKeys.index(key) % 12)
    threeOctave = getEnharmonicScale(naturalRoot, key)
    rootName = threeOctave[naturalIndex] + romanAccidental
    if romanMinor and (chordQuality == "" or chordQuality[0] != 'm') :
      chordQuality = 'm' + chordQuality;    
  
  rootName = convertEnharmonic(rootName, key)    

  # find the right function to convert the chord name to pitch classes
  if doCup :
    functionSelector = qualityCupFunc
  else:
    functionSelector = qualityFunc

  funcIndex = quality.index(chordQuality)
  chordFunc = functionSelector[funcIndex]  
  return processSlashBass(chordFunc(rootName, chordInversion, noRoot), slashBass)



# *****************************************************************************
# All deck functions create a randomized deck of "chord cards" according to the
# type of cards they are asked to include.
# EXAMPLE: The deck() function may include any type of chord,
#          The basicDeck() function returns basic chords only like Major/Min/7
#          The dominantSevenDeck() function returns Dominant Seven chords only
#         ... etc.
#
# By default a simple text chart is created. (A default chart function is used
# if you don't specify an argument to the function.

# Don't get confused, you can just type deck() or basicDeck() or whatever and
# be fine.  You don't have to pass a Charting Function. I did it this way
# to allow myself to create different kinds of charts in the future such as
# say in MusicXML. If I created a MusicXMLChart function, you would then be
# able to type deck(MusicXMLChart) for example - but that is for the future.
# I didn't do that now because I didn't want to creat a dependency on another
# library like music21 . And I wasn't convinced yet that, just for practice,
#that I would really have the need for that feature.

def deck(chartFunc = SimpleTextChart):
  return chartFunc(card)

def basicDeck(chartFunc = SimpleTextChart):
  return chartFunc(basicCard)

def extendedDeck(chartFunc = SimpleTextChart):
  return chartFunc(extendedCard)

def colorfulDeck(chartFunc = SimpleTextChart):
  return chartFunc(colorfulCard)

def diminishedDeck(chartFunc = SimpleTextChart):
  return chartFunc(diminishedCard)

def alteredDeck(chartFunc = SimpleTextChart):
  return chartFunc(alteredCard)

def majorDeck(chartFunc = SimpleTextChart):
  return chartFunc(majorCard)

def minorDeck(chartFunc = SimpleTextChart):
  return chartFunc(minorCard)
  
def dominantSevenDeck(chartFunc = SimpleTextChart):
  return chartFunc(dominantSevenCard)

def minorSevenDeck(chartFunc = SimpleTextChart):
  return chartFunc(minorSevenCard)

def nineDeck(chartFunc = SimpleTextChart):
  return chartFunc(nineCard)

def minorNineDeck(chartFunc = SimpleTextChart):
  return chartFunc(minorNineCard)

def elevenDeck(chartFunc = SimpleTextChart):
  return chartFunc(elevenCard)

def minorElevenDeck(chartFunc = SimpleTextChart):
  return chartFunc(minorElevenCard)

def thirteenDeck(chartFunc = SimpleTextChart):
  return chartFunc(thirteenCard)

def minorThirteenDeck(chartFunc = SimpleTextChart):
  return chartFunc(minorThirteenCard)

def majorSevenDeck(chartFunc = SimpleTextChart):
  return chartFunc(majorSevenCard)

def minorMajorSevenDeck(chartFunc = SimpleTextChart):
  return chartFunc(minorMajorSevenCard)

def majorNineDeck(chartFunc = SimpleTextChart):
  return chartFunc(majorNineCard)

def minorMajorNineDeck(chartFunc = SimpleTextChart):
  return chartFunc(minorNineCard)

def majorThirteenDeck(chartFunc = SimpleTextChart):
  return chartFunc(majorThirteenCard)

def minorMajorThirteenDeck(chartFunc = SimpleTextChart):
  return chartFunc(minorMajorThirteenCard)

def sixDeck(chartFunc = SimpleTextChart):
  return chartFunc(sixCard)

def minorSixDeck(chartFunc = SimpleTextChart):
  return chartFunc(minorSixCard)

def sixNineDeck(chartFunc = SimpleTextChart):
  return chartFunc(sixNineCard)

def minorSixNineDeck(chartFunc = SimpleTextChart):
  return chartFunc(minorSixNineCard)

def diminishedSevenDeck(chartFunc = SimpleTextChart):
  return chartFunc(diminishedSevenCard)

def halfDiminishedDeck(chartFunc = SimpleTextChart):
  return chartFunc(halfDiminishedCard)

def augmentedDeck(chartFunc = SimpleTextChart):
  return chartFunc(augmentedCard)

def augmentedSevenDeck(chartFunc = SimpleTextChart):
  return chartFunc(augmentedSevenCard)

def suspendedDeck(chartFunc = SimpleTextChart):
  return chartFunc(suspendedCard)

def dominantSevenFlatNineDeck(chartFunc = SimpleTextChart):
  return chartFunc(dominantSevenFlatNineCard)
  
def dominantSevenSharpNineDeck(chartFunc = SimpleTextChart):
  return chartFunc(dominantSevenSharpNineCard)

def dominantSevenFlatFiveDeck(chartFunc = SimpleTextChart):
  return chartFunc(dominantSevenFlatFiveCard)

# ==============================================================================
# All "Train" functions return a list of chord names of the type
# indicated as well as their "Cup" voicing
# for the purpose of learning these voicings

def majorTrain():
  SimpleTextVoicing("Major Chords \nCup Shape Interval (1 5 3)", 0, majorCup)
  
def minorTrain():
  SimpleTextVoicing("Minor Chords \nCup Shape Interval (1 5 b3)", 1, minorCup)
  
def dominantSevenTrain():
  SimpleTextVoicing("Dominant Seven Chords \nCup Shape Interval (1 b7 3 5)", 2, dominantSevenCup)   

def minorSevenTrain():
  SimpleTextVoicing("Minor Seven Chords \nCup Shape Interval (1 b7 b3 5)", 3, minorSevenCup)
  
def nineTrain():
  SimpleTextVoicing("Nineth Chords \nCup Shape Interval (1 b7 3 5 9)", 4, nineCup)
 
def minorNineTrain():
  SimpleTextVoicing("Minor Nineth Chords \nCup Shape Interval (1 b7 b3 5 9)", 5, minorNineCup)

def elevenTrain():
  SimpleTextVoicing("Cup Shape Interval (1 3 b7 9 11)", 6, elevenCup)
  
def minorElevenTrain():
  SimpleTextVoicing("Cup Shape Interval (1 b3 b7 9 11)", 7, minorElevenCup)
  
def thirteenTrain():
  SimpleTextVoicing("Cup Shape Interval (1 b7 3 13 9)", 8, thirteenCup)
  
def minorThirteenTrain():
  SimpleTextVoicing("Cup Shape Interval (1 b7 b3 13 9)", 9, minorThirteenCup)

def majorSevenTrain():
  SimpleTextVoicing("Cup Shape Interval (1 7 3 5 )", 10, majorSevenCup)

def minorMajorSevenTrain():
  SimpleTextVoicing("Cup Shape Interval (1 7 b3 5)", 11, minorMajorSevenCup)

def majorNineTrain():
  SimpleTextVoicing("Cup Shape Interval (1 7 3 5 9)", 12, majorNineCup)
  
def minorMajorNineTrain():
  SimpleTextVoicing("Cup Shape Interval (1 7 b3 5 9)", 13, minorMajorNineCup)
  
def majorThirteenTrain():
  SimpleTextVoicing("Cup Shape Interval (1 7 3 13 9)", 14, majorThirteenCup)

def minorMajorThirteenTrain():
  SimpleTextVoicing("Cup Shape Interval (1 7 b3 13 9)", 15, minorMajorThirteenCup)

def sixTrain():
  SimpleTextVoicing("Cup Shape Interval (1 5 3 6)", 16, sixCup)

def minorSixTrain():
  SimpleTextVoicing("Cup Shape Interval (1 5 b3 6)", 17, minorSixCup)  

def sixNineTrain():
  SimpleTextVoicing("Cup Shape Interval (1 5 3 6 9)", 18, sixNineCup)

def minorSixNineTrain():
  SimpleTextVoicing("Cup Shape Interval (1 5 b3 6 9)", 19, minorSixNineCup)  
     
def diminishedSevenTrain():
  SimpleTextVoicing("Cup Shape Interval (1 bb7 b3 b5)", 20, diminishedSevenCup)

def halfDiminishedTrain():
  SimpleTextVoicing("Cup Shape Interval (1 b7 b3 b5)", 21, halfDiminishedCup)

def augmentedTrain():
  SimpleTextVoicing("Cup Shape Interval (1 #5 3)", 22, augmentedCup)

def augmentedSevenTrain():
  SimpleTextVoicing("Cup Shape Interval (1 b7 3 #5)", 23, augmentedSevenCup)

def suspendedTrain():
  SimpleTextVoicing("Cup Shape Interval (1 5 b7 4)", 24, suspendedCup)

def dominantSevenFlatNineTrain():
  SimpleTextVoicing("Cup Shape Interval (1 b7 3 5 b9)", 25, dominantSevenFlatNineCup)

def dominantSevenSharpNineTrain():
  SimpleTextVoicing("Cup Shape Interval (1 b7 3 5 #9)", 26, dominantSevenSharpNineCup)

def dominantSevenFlatFiveTrain():
  SimpleTextVoicing("Cup Shape Interval (1 b7 3 b5)", 27, dominantSevenFlatFiveCup) 


# ==============================================================================
# All "Card" functions return a single chord name of the type indicated for
# purposes of practice.You will usually prefer to use one of the deck
# which return a randomized list of chords

def card():
  return root[random.randint(0,11)] + quality[random.randint(0,27)]

def basicCard():
  return root[random.randint(0,11)] + quality[random.randint(0,3)]

def extendedCard():
  return root[random.randint(0,11)] + quality[random.randint(4,9)]

def colorfulCard():
  return root[random.randint(0,11)] + quality[random.randint(10,19)]

def diminishedCard():
  return root[random.randint(0,11)] + quality[random.randint(19,21)]

def alteredCard():
  return root[random.randint(0,11)] + quality[random.randint(21,27)]

def majorCard():
  return root[random.randint(0,11)] + quality[0]

def minorCard():
  return root[random.randint(0,11)] + quality[1]

def dominantSevenCard():
  return root[random.randint(0,11)] + quality[2]

def minorSevenCard():
  return root[random.randint(0,11)] + quality[3]

def nineCard():
  return root[random.randint(0,11)] + quality[4]

def minorNineCard():
  return root[random.randint(0,11)] + quality[5]

def elevenCard():
  return root[random.randint(0,11)] + quality[6]

def minorElevenCard():
  return root[random.randint(0,11)] + quality[7]

def thirteenCard():
  return root[random.randint(0,11)] + quality[8]

def minorThirteenCard():
  return root[random.randint(0,11)] + quality[9]

def majorSevenCard():
  return root[random.randint(0,11)] + quality[10]

def minorMajorSevenCard():
  return root[random.randint(0,11)] + quality[11]

def majorNineCard():
  return root[random.randint(0,11)] + quality[12]

def minorMajorNineCard():
  return root[random.randint(0,11)] + quality[13]

def majorThirteenCard():
  return root[random.randint(0,11)] + quality[14]

def minorMajorThirteenCard():
  return root[random.randint(0,11)] + quality[15]

def sixCard():
  return root[random.randint(0,11)] + quality[16]

def minorSixCard():
  return root[random.randint(0,11)] + quality[17]

def sixNineCard():
  return root[random.randint(0,11)] + quality[18]

def minorSixNineCard():
  return root[random.randint(0,11)] + quality[19]

def diminishedSevenCard():
  return root[random.randint(0,11)] + quality[20]

def halfDiminishedCard():
  return root[random.randint(0,11)] + quality[21]

def augmentedCard():
  return root[random.randint(0,11)] + quality[22]

def augmentedSevenCard():
  return root[random.randint(0,11)] + quality[23]

def suspendedCard():
  return root[random.randint(0,11)] + quality[24]

def dominantSevenFlatNineCard():
  return root[random.randint(0,11)] + quality[25]

def dominantSevenSharpNineCard():
  return root[random.randint(0,11)] + quality[26]

def dominantSevenFlatFiveCard():
  return root[random.randint(0,11)] + quality[27]


# ==============================================================================
# All "Cup" functions return the proper notes in order (bottom to top) for this
# type of voicing for a single chord name of the type indicated.

def majorCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [7,4], chordInversion, isRootless)

def minorCup(chordRoot, chordInversion = 0, isRootless = False):
  return voiceMe(chordRoot, [7,3], chordInversion, isRootless)   

def dominantSevenCup(chordRoot, chordInversion = 0, isRootless = False):
  return voiceMe(chordRoot, [10,4,7], chordInversion, isRootless)

def minorSevenCup(chordRoot, chordInversion = 0, isRootless = False):
  return voiceMe(chordRoot, [10,3,7], chordInversion, isRootless)

def nineCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [10,4,7,14], chordInversion, isRootless)

def minorNineCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [10,3,7,14], chordInversion, isRootless)

def elevenCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [4,10,14,17], chordInversion, isRootless)

def minorElevenCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [3,10,14,17], chordInversion, isRootless) 

def thirteenCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [10,4,9,14], chordInversion, isRootless)

def minorThirteenCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [10,3,9,14], chordInversion, isRootless)

def majorSevenCup(chordRoot, chordInversion = 0, isRootless = False):
  return voiceMe(chordRoot, [11,4,7], chordInversion, isRootless)

def minorMajorSevenCup(chordRoot, chordInversion = 0, isRootless = False):
  return voiceMe(chordRoot, [11,3,7], chordInversion, isRootless)

def majorNineCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [11,4,7,14], chordInversion, isRootless)

def minorMajorNineCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [11,3,7,14], chordInversion, isRootless)  

def majorThirteenCup(chordRoot, chordInversion = 0, isRootless = False):
   return voiceMe(chordRoot, [11,4,9,14], chordInversion, isRootless)

def minorMajorThirteenCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [11,3,9,14], chordInversion, isRootless)

def sixCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [7,4,9], chordInversion, isRootless)

def minorSixCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [7,3,9], chordInversion, isRootless) 

def sixNineCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [7,4,9,14], chordInversion, isRootless)

def minorSixNineCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [7,3,9,14], chordInversion, isRootless)

def diminishedSevenCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [9,3,6], chordInversion, isRootless)

def halfDiminishedCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [10,3,6], chordInversion, isRootless)

def augmentedCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [8,4], chordInversion, isRootless)

def augmentedSevenCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [10,8,4], chordInversion, isRootless)

def suspendedCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [7,10,5], chordInversion, isRootless) 

def dominantSevenFlatNineCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [10,4,7,13], chordInversion, isRootless)

def dominantSevenSharpNineCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [10,4,7,15], chordInversion, isRootless)

def dominantSevenFlatFiveCup(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [10,4,6], chordInversion, isRootless)

# ==============================================================================
# All "Triad" functions return the proper notes in order for a simple or
# extended Triad from music theory

def major(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [4,7], chordInversion, isRootless)

def minor(chordRoot, chordInversion = 0, isRootless = False):
  return voiceMe(chordRoot, [3,7], chordInversion, isRootless)   

def dominantSeven(chordRoot, chordInversion = 0, isRootless = False):
  return voiceMe(chordRoot, [4,7,10], chordInversion, isRootless)

def minorSeven(chordRoot, chordInversion = 0, isRootless = False):
  return voiceMe(chordRoot, [3,7,10], chordInversion, isRootless)

def nine(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [4,7,10,14], chordInversion, isRootless)

def minorNine(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [3,7,10,14], chordInversion, isRootless)

def eleven(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [4,10,14,17], chordInversion, isRootless)

def minorEleven(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [3,10,14,17], chordInversion, isRootless) 

def thirteen(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [4,10,14,9], chordInversion, isRootless)

def minorThirteen(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [3,10,14,9], chordInversion, isRootless)

def majorSeven(chordRoot, chordInversion = 0, isRootless = False):
  return voiceMe(chordRoot, [4,7,11], chordInversion, isRootless)

def minorMajorSeven(chordRoot, chordInversion = 0, isRootless = False):
  return voiceMe(chordRoot, [3,7,11], chordInversion, isRootless)

def majorNine(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [4,7,11,14], chordInversion, isRootless)

def minorMajorNine(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [3,7,11,14], chordInversion, isRootless)  

def majorThirteen(chordRoot, chordInversion = 0, isRootless = False):
   return voiceMe(chordRoot, [4,11,14,9], chordInversion, isRootless)

def minorMajorThirteen(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [3,11,14,9], chordInversion, isRootless)

def six(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [4,7,9], chordInversion, isRootless)

def minorSix(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [3,7,9], chordInversion, isRootless) 

def sixNine(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [4,7,9,14], chordInversion, isRootless)

def minorSixNine(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [3,7,9,14], chordInversion, isRootless)

def diminishedSeven(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [3,6,9], chordInversion, isRootless)

def halfDiminished(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [3,6,10], chordInversion, isRootless)

def augmented(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [4,8], chordInversion, isRootless)

def augmentedSeven(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [4,8,10], chordInversion, isRootless)

def suspended(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [7,10,5], chordInversion, isRootless) 

def dominantSevenFlatNine(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [4,7,10,13], chordInversion, isRootless)

def dominantSevenSharpNine(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [4,7,10,15], chordInversion, isRootless)

def dominantSevenFlatFive(chordRoot, chordInversion = 0, isRootless = False):
    return voiceMe(chordRoot, [4,6,10], chordInversion, isRootless)

qualityFunc = [major, minor, dominantSeven, minorSeven, nine, minorNine, eleven,
           minorEleven, thirteen, minorThirteen, majorSeven, minorMajorSeven, 
           majorNine, minorMajorNine, majorThirteen, minorMajorThirteen, six, 
           minorSix, sixNine, minorSixNine, diminishedSeven, halfDiminished,
           augmented, augmentedSeven, suspended, dominantSevenFlatNine,
           dominantSevenSharpNine, dominantSevenFlatFive]


qualityCardFunc = [majorCard, minorCard, dominantSevenCard, minorSevenCard, nineCard, minorNineCard, elevenCard,
           minorElevenCard, thirteenCard, minorThirteenCard, majorSevenCard, minorMajorSevenCard, 
           majorNineCard, minorMajorNineCard, majorThirteenCard, minorMajorThirteenCard, sixCard, 
           minorSixCard, sixNineCard, minorSixNineCard, diminishedSevenCard, halfDiminishedCard,
           augmentedCard, augmentedSevenCard, suspendedCard, dominantSevenFlatNineCard,
           dominantSevenSharpNineCard, dominantSevenFlatFiveCard]


qualityCupFunc = [majorCup, minorCup, dominantSevenCup, minorSevenCup, nineCup, 
           minorNineCup, elevenCup, minorElevenCup, thirteenCup, 
           minorThirteenCup, majorSevenCup, minorMajorSevenCup, majorNineCup, 
           minorMajorNineCup, majorThirteenCup, minorMajorThirteenCup, sixCup, 
           minorSixCup, sixNineCup, minorSixNineCup, diminishedSevenCup, 
           halfDiminishedCup, augmentedCup, augmentedSevenCup, suspendedCup, 
           dominantSevenFlatNineCup, dominantSevenSharpNineCup, 
           dominantSevenFlatFiveCup]           



qualityTrainFunc = [majorTrain, minorTrain, dominantSevenTrain, minorSevenTrain, nineTrain, minorNineTrain, elevenTrain,
           minorElevenTrain, thirteenTrain, minorThirteenTrain, majorSevenTrain, minorMajorSevenTrain, 
           majorNineTrain, minorMajorNineTrain, majorThirteenTrain, minorMajorThirteenTrain, sixTrain, 
           minorSixTrain, sixNineTrain, minorSixNineTrain, diminishedSevenTrain, halfDiminishedTrain,
           augmentedTrain, augmentedSevenTrain, suspendedTrain, dominantSevenFlatNineTrain,
           dominantSevenSharpNineTrain, dominantSevenFlatFiveTrain]


def help():
  print("\n\nQuick Reference. Please refer to the documentation for a ")
  print("detailed explanation: \n")
  print("Deck Methods: Imagine a deck of flashcards with ")
  print("the name of a chord on each card. Using the Carl.deck() method ")
  print("essentially shuffles this immaginary deck and gives you a  ")
  print("practice exercise. Other similar methods will limit the types ")
  print("of chords that the deck contains. Examples include: \n") 
  print("     basicDeck() extendedDeck() colorfulDeck() diminishedDeck() ")
  print("     alteredDeck() majorDeck() minorDeck() diminishedDeck() ")
  print("     dominantSevenDeck() minorSevenDeck() nineDeck() ")
  print("     minorNineDeck() elevenDeck() minorElevenDeck() ")
  print("     thirteenDeck() minorThirteenDeck() majorSevenDeck() ")
  print("     minorMajorSevenDeck() majorNineDeck() minorMajorNineDeck() ")
  print("     majorThirteenDeck() minorMajorThirteenDeck() sixDeck() ")
  print("     minorSixDeck() sixNineDeck() minorSixNineDeck() ")
  print("     diminishedSevenDeck() halfDiminishedDeck() augmentedDeck() ")
  print("     augmentedSevenDeck() suspendedDeck() dominantSevenFlatNineDeck() ")
  print("     dominateSevenSharpNineDeck() dominantSevenFlatFiveDeck() ")
  print("\n")
  


# *****************************************************************************
# *****************************************************************************
# *****************************************************************************
# *****************************************************************************
# PUBLIC INTERFACE

def commonQualities() :
  return str(quality)

def shuffle():
   deck()

def shuffle(chordQuality):
   if chordQuality == "":
      deck()
   else:
    i = 0
    while i < len(quality):
      if quality[i] == chordQuality:
        return SimpleTextChart(qualityCardFunc[i])
      i = i + 1

    print("Requested Chord Quality not found. Use one of: ")
    return commonQualities()


def train(chordQuality):
   if chordQuality == "":
      deck()
   else:
    i = 0
    while i < len(quality):
      if quality[i] == chordQuality:
        return qualityTrainFunc[i]()
      i = i + 1

    print("Requested Chord Quality not found. Use one of: ")
    return commonQualities()       
         

print("\n-------------------------------------")
print("Carl: Gremlin, specializing in chords")
print("Type Carl.help() if needed.")
print("-------------------------------------\n")

