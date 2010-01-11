"""
Convenience functions for getting specific info out of a config file
"""

INFO_L = "L"
INFO_lmax = "lmax"
INFO_RadialGrid = "radial_grid"
INFO_Eigenvalues = "eigenvalues"

def GetConfigInfo(conf, infoId):
	if infoId == INFO_L:
		indexIterator = conf.AngularRepresentation.index_iterator
		Llist = array([idx.L for idx in indexIterator])
		L = Llist[0]
		if any(Llist != L):
			raise Exception("L is not unique for the given config (%s)" % Llist)
		return L

	elif infoId == INFO_lmax:
		indexIterator = conf.AngularRepresentation.index_iterator
		lmax = max(array([idx.l1 for idx in indexIterator]))
		return lmax

	elif infoId == INFO_RadialGrid:
		return GetRadialGrid(config=conf)

	else:
		raise Exception("Unknown infoId %s" % infoId)




