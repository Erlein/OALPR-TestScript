import json					# JSON parsing
import argparse				# Argument parser
import os					# OS interaction
import time					# Timing
from getpass import getuser	# To get username
from openalpr import Alpr	# OpenALPR library. Importing ALPR only, as this is only used feature.

begin = time.perf_counter()		# Start timer for init and total time.

# Argument parsing
ap = argparse.ArgumentParser()	# Init argparser
ap.add_argument("-i", "--input", 	dest="input",	type=str,	required=True,	help="Input directory path (required).")
ap.add_argument("-o", "--output",	dest="outDir",	type=str,	required=False,	default="results.csv", 	help="Output file(path).")
args = ap.parse_args()

# Validate path
if os.path.isdir(args.input):	# Check the path is a directory.
	print("Given path is a directory.")
	for fname in os.listdir(args.input):	# Validate presence of at least one jpg image.
		if fname.endswith(".jpg"):
			print("Directory contains at least one jpg image.")
			break
	else:
		exit("ERROR: No jpg files found in directory!")
else:
	ap.error("ERROR: Provide path to a directory containing images using -i flag!")

# Initialize ALPR engine
## Use two lines below rather than third if openalpr is installed in home rather than /etc
# uname = getuser()	# Get username
#alpr = Alpr("eu", "/home/"+ uname +"/openalpr/config/openalpr.conf.defaults", "/home/"+ uname +"/openalpr/runtime_data") # Dynamic uname
alpr = Alpr("eu", "/etc/openalpr/openalpr.conf", "/usr/share/openalpr/runtime_data")
if not alpr.is_loaded():
    exit("Error loading openalpr!")

# Prepare output file
if args.outDir:
	outFile = os.open(args.outDir, os.O_CREAT|os.O_RDWR)

# Calculate init time and write to file if relevant.
it = format(time.perf_counter() - begin, ".3f")	# Calculate init-time	(Alternate formatting: round(num, 3))
print("Init time taken:", it)
if args.outDir:
	itStr = str(it) + "\n"
	os.write(outFile, (str.encode(itStr))) # Write init time to file.

# Variables for score-keeping
imgCnt  = 0		# Counter for images
dets 	= 0		# Coutner for detections

# Loop directory and run ALPR on contents
path = os.walk(args.input)	# Walk dir
for r, dir, files in path:
	for file in files:
		if ".jpg" in file:					# Only process jpg images (might extend to more filetypes but p not nescessary)
			imgCnt += 1
			start = time.perf_counter()
			out = alpr.recognize_file(args.input + file)	# Perform ALPR on image
			dt = format(time.perf_counter() - start, ".3f")
			if out['results']:		# Check if detection returned any results.
				dets += 1
				outson = json.dumps(out['results'][0]['plate'], indent=4)[1:-1]
				print("\n" + file)
				print(outson) # Print result and confidence
				print("Detection time taken:", dt)
				if args.outDir:	# Write to file if argument given
					outStr = file + "," + outson + "," + str(dt) + "\n"
					os.write(outFile, str.encode(outStr))
			else:					# Else, return as no result found, and write to file.
				print("\n" + file)
				print("No plate found.")
				print("Detection time taken:", dt)
				if args.outDir:
					os.write(outFile, str.encode(file + ",NoPlateFound," + str(dt) + "\n"))		# Printing filename and failed det.

# Printing statistics for entire run
totTime = format(time.perf_counter() - begin, ".3f")
print("\nTotal images:", imgCnt)
print("Plates detected:", dets)
print("Proportion:" ,str(round((dets / imgCnt)*100,3)) + "%")
print("Time taken:", totTime, "\n")
outStr = "totTime," + str(totTime)
os.write(outFile, str.encode(outStr))

# Deinit ALPR engine
alpr.unload()
os.close(outFile)
