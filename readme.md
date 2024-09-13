# TMM SCRAPER TO GET ALL THE INVOICES SENT TO THE SITE


## Specifications



- ### The scraper must be written in Python 3.10.12, the libraries were managed with pip 23.2.1
  
## Scaffold



### 1. Be sure to use python 3.10.12 or major versions (with an appropriate pip version)
### 2. Install all the libraries in the requirements.txt file (if you use pip run `pip install -r requirements.txt`)
### 3. Rename the file '.env.dist' into '.env' and fill the variables with the correct values (please, keep the single quote as trailer and header of each variables entered)
### 4. Rename the file 'pfi.json.dist' into 'pfi.json' and fill it with your pfi
### 5. Run the command `python main.py` to start the scraper

## Output



## The output of the scraper will be three different excel files:
### - currentYearAmount.xlsx: This file will contain the total amount of invoices which have been sent since the start of the last edition (first October of the previous year) until the current date.
### - allAmount.xlsx: This file will contain the total amount of invoices which have been sent since the start of the program.
### - moneyToSpend.xlsx: This file will contain the total amount of money that you need to spend before the end of the edition.