from arelle import Cntlr

cntlr = Cntlr.Cntlr()
wc = cntlr.webCache

url = "http://archprod.service.eogs.dk/taxonomy/20241001/entryDanishGAAPBalanceSheetAccountFormIncomeStatementByNatureIncludingManagementsReviewStatisticsAndTax20241001.xsd"

print("URL:", url)
print("normalizeUrl:", wc.normalizeUrl(url))
print("cache filepath:", wc.urlToCacheFilepath(url))
