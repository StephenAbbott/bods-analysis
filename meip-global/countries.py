"""ISO3 -> short English name for the jurisdictions that appear in tables and charts.
Names follow the MEIP spreadsheet's Country_Code_mapping sheet, shortened for charts."""
NAMES = {
 'USA':'United States','GBR':'United Kingdom','FRA':'France','DEU':'Germany','CHN':'China','NLD':'Netherlands',
 'CAN':'Canada','AUS':'Australia','MEX':'Mexico','ESP':'Spain','IND':'India','CYM':'Cayman Islands','LUX':'Luxembourg',
 'ITA':'Italy','BRA':'Brazil','ARE':'United Arab Emirates','JPN':'Japan','SGP':'Singapore','IRL':'Ireland','CHE':'Switzerland',
 'HKG':'Hong Kong','BMU':'Bermuda','JEY':'Jersey','VGB':'British Virgin Islands','BEL':'Belgium','SWE':'Sweden','DNK':'Denmark',
 'AUT':'Austria','POL':'Poland','MYS':'Malaysia','KOR':'South Korea','CHL':'Chile','ZAF':'South Africa','NOR':'Norway',
 'NZL':'New Zealand','MUS':'Mauritius','MLT':'Malta','CYP':'Cyprus','LBR':'Liberia','CUW':'Curaçao','TWN':'Taiwan',
 'BHS':'Bahamas','LIE':'Liechtenstein','MHL':'Marshall Islands','SYC':'Seychelles','GIB':'Gibraltar','WSM':'Samoa',
 'BLZ':'Belize','AIA':'Anguilla','VCT':'St Vincent & Grenadines','GUY':'Guyana','MCO':'Monaco','NRU':'Nauru',
 'SAU':'Saudi Arabia','FIN':'Finland','RUS':'Russia','ISR':'Israel','PHL':'Philippines','THA':'Thailand','IDN':'Indonesia',
}
def name(iso3): return NAMES.get(iso3, iso3 or 'Not given')
