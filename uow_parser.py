"""
	uow_parser.py
	author: Erwin Leonardy

	input : .html file 
	output: .ics file

	This is a python script which enables you
	to create an .ics file which contains all
	of the time and location of the classes
	found in the .html file
"""

import os, fnmatch
from bs4 import BeautifulSoup
from collections import OrderedDict

# variable declarations
timeZone = ';TZID=Asia/Singapore'
semester = ''
universityLevel = ''
universityName = ''
lecturers = list()
noOfClasses = list()

"""
	Function Definitions
"""
# get the source HTML filename
def getInputFileName (allFiles):
	# asks user for the HTML file to open
	count = 1
	print ('Please enter the file you want:')

	# loop through all of the available .html files
	for file in allFiles:
		# get only the filename
		file = os.path.basename(file)

		# print each of the file
		print ("   {}) {}".format(count, file))
		count += 1

	max = len(allFiles)

	# loop till user gives correct input
	while True:
		try:
			# prompt for filename
			choice = int(input('\nEnter a number > '))

		# if a character is given
		except ValueError:
			print ('Please only enter a digit!')
			continue

		# option (1)
		# but, user didn't choose 1
		if max == 1 and (choice != 1):
			print ('Invalid Input! Enter the value 1!\n')
			continue

		# option (1 , 2, 3)
		# but, user didn't choose (1 or 2 or 3)
		elif not choice in range (1, max):
			if choice > max:
				print ("Invalid input! Enter a value between 1 - {}".format(max))
				continue

		return os.path.abspath(allFiles[choice-1])

# get the name of the file for the .ics
def getExportFileName (soup):
	# find the filename
	lines = soup.find_all("span")

	for line in lines:
		if ('Quarter' in line.text):
			break

	# remove the unecessary part
	line = line.text.replace('\n','').split('|')

	# get the filename
	# remove the spaces in between
	global semester
	semester = line[0]

	global universityLevel
	universityLevel = line[1]

	global universityName
	universityName = line[2]

	filename = semester + '_' + universityName + '.ics'
	filename = filename.replace(' ','')

	return filename

# parse all of the module names and codes
def parseModuleName (soup):
	# get all tags with PAGROUPDIVIDER class
	lines = soup.find_all("td", {"class" : "PAGROUPDIVIDER"})

	# get the module name & code
	modules = list()

	# loop through the whole soup objects
	for entry in lines:
		# get the content
		course = entry.text

		# ignore non-module codes
		# ignore Term Break
		if  ((not 'Important Time Periods' in course)	and
		     (not 'Public Holidays' in course)			and
		     (not 'TB' in course)):
			# convert '&amp;' ==> '&'
			modules.append(course)

	# duplicate modules	 
	"""
	N.B. _ is traditionally used as a placeholder variable name where you do
       	not want to do anything with the contents of the variable. In this case,
       	it is just used to generate two values for every time round the outer 
	loop.
	"""
	modules =  [val for val in modules for _ in (0, 1)]

	return modules

# parse time and classes
def parseClass (soup, modules):
	# get all tags with PSLEVEL3GRIDROW class
	lines = soup.find_all("td", {"class": "PSLEVEL3GRIDROW"})

	global lecturers
	global noOfClasses
	classes = list()
	Idx = -1
	
	# loop through all the lines
	for line in lines:
		# get the content
		line = line.find('span')

		# ignore useless HTML tags
		# ignore term break
		if ((line != None)	and 
			(not 'TB' in line.text)):

			# determine whether it is a lecture or tutorial
			if (line.has_attr('title')):
				section = line.text
				noOfClasses.append(0);
				Idx += 1

			# get time
			elif ("MTG_SCHED" in line['id']):
				time = parseTime(line.text)

			# get location
			elif ("MTG_LOC" in line['id']):
				location = line.text

			# get lecturer
			elif ("DERIVED_CLS_DTL_SSR_INSTR_LONG" in line['id']):
				# ignore staff
				if (not 'Staff' in line.text):
					lecturer = line.text
					lecturers.append(lecturer)

			# get date
			elif ("MTG_DATES" in line['id']):
				date = parseDate(line.text)
				noOfClasses[Idx] += 1
				
				# store inside the list
				classes.append([modules[Idx], section, date,
								time, location, lecturer])

	# return the list
	return classes	

# write the list to the calendar file
def writeICS (classes, outputFileName):
	f = open (outputFileName, "w")

	# write header
	str = 'BEGIN:VCALENDAR\n'
	str += 'VERSION:2.0\n'

	# write content
	for line in classes:
		title = line[0] + ' (' + line[1] + ')'
		date = line[2]
		startTime = line[3][0]
		endTime = line[3][1]
		location = line[4]
		lecturer = line[5]

		str += 'BEGIN:VEVENT\n'
		str += 'DTSTART' + timeZone + ':' + date + 'T' + startTime + '00\n'
		str += 'DTEND' + timeZone + ':' + date + 'T' + endTime + '00\n'
		str += 'SUMMARY:' + title + '\n'
		str += 'DESCRIPTION: Lecturer = ' + lecturer + '\n'
		str += 'LOCATION:' + location + '\n'
		str += 'END:VEVENT\n'	

	# write footer
	str += 'END:VCALENDAR'
	f.write(str)
	f.close()

# print info to the screen
def printInfo (modules):
	global noOfClasses
	classIdx = 0

	global lecturers
	lecturers = list(OrderedDict.fromkeys(lecturers))
	lecturerIdx = 0

	modules = list(OrderedDict.fromkeys(modules))

	# when lecture and tutorial teacher is the same
	if (len(lecturers) == 2):
		lecturers =  [val for val in lecturers for _ in (0, 1)]

	print ('\n============================================')
	print ('\t\tInformation')
	print ('============================================')
	print ('Semester\t : ' + semester)
	print ('University Name\t :' + universityName)
	print ('Degree Type\t :' + universityLevel)

	print ('\n============================================')
	print ('\t      Subjects Offered')
	print ('============================================')

	for module in modules:
		print ('- ' + module)

		print ('  Lecture Teacher  : ' + lecturers[lecturerIdx].title())
		lecturerIdx += 1

		print ('  Tutorial Teacher : ' + lecturers[lecturerIdx].title())
		lecturerIdx += 1

		print ('  No. of Lectures  : {} classes'.format(noOfClasses[classIdx]))
		classIdx += 1

		# check when there is tutorial or not
		if (0 <= classIdx < len(noOfClasses)):
			print ('  No. of Tutorials : {} classes\n'.format(noOfClasses[classIdx]))
			classIdx += 1
		else:
			print ('  No. of Tutorials : 0 class\n')
		
	
"""
	HELPER FUNCTIONS
"""
# parse DD/MM/YYYY -> YYYYMMDD
def parseDate (date):
	# remove duplicate dates
	date = date[-10:]

	# get individual elements
	year  = date[6:]
	month = date[3:5]
	day   = date[:2]

	# append final format 
	date = year + month + day	
	return date

# parse HH:MM(AM) - HH:MM(AM) -> (HHMMSS, HHMMSS)
def parseTime (time):
	newTime = list()

	# remove the day
	time = time[3:]
	time = time.replace(' ', '')

	# get the start time and end time
	time = time.split('-')

	# convert start time and end time
	for eachTime in time:
		#  9.59PM -> 09.59PM
       	# 10.00PM -> 10.00PM (remains the same) 	
		if (len(eachTime) <= 6):
			eachTime = '0' + eachTime	

		# convert 12 Hours -> 24 Hours
		# remove the ':' seperator
		twentyFourFormat = convertTo24(eachTime).replace(':','')
		newTime.append(twentyFourFormat)

	return newTime

# convert 12 Hours format to 24 Hours format
def convertTo24 (temp):
	# check if the last two elements of time
	# is AM and first two elements is 12
	if temp[-2:] == "AM" and temp[:2] == "12":
		return "00" + temp[2:-2]

	# remove the AM
	elif temp[-2:] == "AM":
		return temp[:-2]

	# check if the last two elements of time
	# is PM and first two elements is 12
	elif temp[-2:] == "PM" and temp[:2] == "12":
		return temp[:-2]

	else:
		# add 12 to hours and remove PM
		return str(int(temp[:2]) + 12) + temp[2:5]

# returns all the html file in the directory
def find (pattern, path):
	result = []
	for root, dirs, files in os.walk(path):
		for name in files:
			if fnmatch.fnmatch(name, pattern):
				result.append(root + '/' + name)
	return result

"""
	MAIN FUNCTION
"""
# find all HTMl files in the current working directory
currentPath = os.getcwd()
allFiles = find ('*.html', currentPath)

# if there is at least a HTMl file
if allFiles :
	# print header
	print ('\n============================================')
	print ('\tSIM - UOW IT Timetable Parser')
	print ('\t    By: Erwin Leonardy')
	print ('============================================\n')

	# prompt users for filename	
	filename = getInputFileName(allFiles)

	# use beautiful soup to parse the HTML Tags
	soup = BeautifulSoup (open(filename), "html.parser")

	# get the module names
	modules = parseModuleName(soup)

	# get the time and classes
	classes = parseClass (soup, modules)

	# if the html file is incorrect
	if (not classes):
		print ('\n================== ERROR ==================')
		print ('\tCorrupted or incorrect HTML!')
		print ('===========================================\n')

	else:
		# get the exportFileName
		outputFileName = getExportFileName(soup)

		# print info 
		printInfo(modules)

		# write to .ics file
		writeICS (classes, outputFileName)

		# print footer
		print ('================= SUCCESS ==================')
		print ('\t    .ics file exported!')
		print ('============================================\n')

# if there is no HTML file
else :
	print ('\n=================== ERROR ===================')
	print ('No HTML file found! Ensure that there')
	print ('is a HTML file in the current directory!')
	print ('=============================================\n')
