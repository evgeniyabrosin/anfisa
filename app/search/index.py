#===============================================
class Index:
    def __init__(self, data_set, legend):
        self.mDataSet = data_set
        self.mLegend  = legend
        self.mRecords = []
        self.mFilterCache = dict()
        for rec_no in range(self.mDataSet.getSize()):
            rec = self.mLegend.getColCount() * [None]
            self.mLegend.fillRecord(
                self.mDataSet.getRecData(rec_no), rec)
            self.mRecords.append(rec)
        for filter_name in self.mLegend.getFilterNames():
            self.cacheFilter(filter_name,
                self.mLegend.getFilterConditions(filter_name))

    def updateRulesEnv(self):
        for rec_no, rec in enumerate(self.mRecords):
            self.mLegend.updateRulesRecordPart(
                self.mDataSet.getRecData(rec_no), rec)
        to_update = []
        for filter_name, filter_info in self.mFilterCache.items():
            if any([cond_info[1] == "Rules"
                    for cond_info in filter_info[0]]):
                to_update.append(filter_name)
        for filter_name in to_update:
            self.cacheFilter(filter_name,
                self.mFilterCache[filter_name][0])

    def getLegend(self):
        return self.mLegend

    @staticmethod
    def not_NONE(val):
        return val is not None

    @staticmethod
    def numeric_LE(the_val):
        return lambda val: val is not None and val >= the_val

    @staticmethod
    def numeric_GE(the_val):
        return lambda val: val is not None and val <= the_val

    @staticmethod
    def numeric_LE_U(the_val):
        return lambda val: val is None or val >= the_val

    @staticmethod
    def numeric_GE_U(the_val):
        return lambda val: val is None or val <= the_val

    @staticmethod
    def enum_OR(base_idx_set):
        return lambda idx_set: len(idx_set & base_idx_set) > 0

    @staticmethod
    def enum_AND(base_idx_set):
        all_len = len(base_idx_set)
        return lambda idx_set: len(idx_set & base_idx_set) == all_len

    @staticmethod
    def enum_NOT(base_idx_set):
        return lambda idx_set: len(idx_set & base_idx_set) == 0

    @staticmethod
    def enum_ONLY(base_idx_set):
        return lambda idx_set: (len(idx_set) > 0 and
            len(idx_set - base_idx_set) == 0)

    def _applyCondition(self, rec_no_seq, cond_info):
        if cond_info[0] == "numeric":
            unit_name, ge_mode, the_val, use_undef = cond_info[1:]
            if ge_mode > 0:
                cmp_func = (self.numeric_GE_U(the_val) if use_undef
                    else self.numeric_GE(the_val))
            elif ge_mode == 0:
                cmp_func = (self.numeric_LE_U(the_val) if use_undef
                    else self.numeric_LE(the_val))
            elif use_undef is False:
                cmp_func = self.not_NONE
            cond_f = self.mLegend.getUnit(unit_name).recordCondFunc(
                cmp_func)
        elif cond_info[0] == "enum":
            unit_name, filter_mode, variants = cond_info[1:]
            if filter_mode == "AND":
                enum_func = self.enum_AND
            elif filter_mode == "ONLY":
                enum_func = self.enum_ONLY
            elif filter_mode == "NOT":
                enum_func = self.enum_NOT
            else:
                enum_func = self.enum_OR
            cond_f = self.mLegend.getUnit(unit_name).recordCondFunc(
                enum_func, variants)
        else:
            assert False
        flt_rec_no_seq = []
        for rec_no in rec_no_seq:
            if cond_f(self.mRecords[rec_no]):
                flt_rec_no_seq.append(rec_no)
        return flt_rec_no_seq

    def _iterRecords(self, rec_no_seq):
        return [self.mRecords[rec_no]
            for rec_no in rec_no_seq]

    def evalConditions(self, conditions):
        rec_no_seq = range(self.mDataSet.getSize())[:]
        for cond_info in conditions:
            rec_no_seq = self._applyCondition(rec_no_seq, cond_info)
            if len(rec_no_seq) == 0:
                break
        return rec_no_seq

    def checkResearchBlock(self, conditions):
        for cond_info in conditions:
            if self.mLegend.getUnit(cond_info[1]).checkResearchBlock(False):
                return True
        return False

    def cacheFilter(self, filter_name, conditions):
        self.mFilterCache[filter_name] = (
            conditions, self.evalConditions(conditions),
            self.checkResearchBlock(conditions))

    def dropFilter(self, filter_name):
        if filter_name in self.mFilterCache:
            del self.mFilterCache[filter_name]

    def getFilterList(self, research_mode):
        ret = []
        for filter_name, flt_info in self.mFilterCache.items():
            if filter_name.startswith('_'):
                continue
            ret.append([filter_name, self.mLegend.hasFilter(filter_name),
                research_mode or not flt_info[2]])
        return sorted(ret)

    def makeStatReport(self, filter_name, research_mode,
            conditions = None):
        rec_no_seq = self.getRecNoSeq(filter_name, conditions)
        report = {
            "stat-list": self.mLegend.collectStatJSon(self._iterRecords(
                rec_no_seq), research_mode),
            "filter-list": self.getFilterList(research_mode),
            "cur-filter": filter_name}
        if (filter_name and filter_name in self.mFilterCache and
                not filter_name.startswith('_')):
            report["conditions"] = self.mFilterCache[filter_name][0]
        return report

    def getRecNoSeq(self, filter_name = None, conditions = None):
        if filter_name is None and conditions:
            return self.evalConditions(conditions)
        if filter_name in self.mFilterCache:
            return self.mFilterCache[filter_name][1]
        return range(self.mDataSet.getSize())[:]

    def getRecFilters(self, rec_no):
        ret0, ret1 = [], []
        for filter_name, flt_info in self.mFilterCache.items():
            if (not filter_name.startswith('_') and
                    rec_no in flt_info[1]):
                if self.mLegend.hasFilter(filter_name):
                    ret0.append(filter_name)
                else:
                    ret1.append(filter_name)
        return sorted(ret0) + sorted(ret1)
