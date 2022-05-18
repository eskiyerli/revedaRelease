# Symbol and Schematic Labels
## Symbol Labels
There are three types of labels:

1. **Normal**: These type of labels is just adding some notes on the text. 
They are not used in netlisting.
2. **NLPLabel**: These types of labels are evaluated using simple rules. 
	Their format is:

	[@propertyName:propertyName=%:propertyName=defaultValue]

	The parts of the NLPLabel is separated by columns(:). Note that 
	only **@propertyName** part is mandatory. The second and third parts
	may not exist in all NLPLabels. 

	If only first part exists, there are a limited number of 

	If the second part exists, it is value is determined  