"""Offshore financial centres as identified by
Garcia-Bernardo, J., Fichtner, J., Takes, F. W. & Heemskerk, E. M. (2017).
Uncovering Offshore Financial Centers: Conduits and Sinks in the Global Corporate
Ownership Network. Scientific Reports 7, 6246. https://doi.org/10.1038/s41598-017-06322-9
Sinks: Table 1 (24 jurisdictions, ordered by sink centrality). Conduits: the five
distinct conduit-OFCs named in the text / Table 2. Copied verbatim (ISO2 -> ISO3).
The classification is based on 2015 Orbis ownership data."""
SINKS = ['VGB','TWN','JEY','BMU','CYM','WSM','LIE','CUW','MHL','MLT','MUS','LUX','NRU','CYP','SYC','BHS',
         'BLZ','GIB','AIA','LBR','VCT','GUY','HKG','MCO']
CONDUITS = ['NLD','GBR','CHE','SGP','IRL']
assert len(SINKS) == 24 and len(CONDUITS) == 5
