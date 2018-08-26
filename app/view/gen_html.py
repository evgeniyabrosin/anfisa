#===============================================
def formTopPage(output, title, html_base,
        data_set_name, data_set_names, modes):
    params = {
        "title": title,
        "data-set": data_set_name,
        "modes": modes,
        "data-set-list": '\n'.join(
            ['<option value="%s">%s</option>' % (set_name, set_name)
            for set_name in sorted(data_set_names)]),
        "html-base": (' <base href="%s" />' % html_base)
            if html_base else ""}

    print >> output, '''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <title>%(title)s</title>
    %(html-base)s
    <link rel="stylesheet" href="anf.css" type="text/css" media="all"/>
    <script type="text/javascript" src="anf.js"></script>
    <script type="text/javascript" src="filters.js"></script>
    <script type="text/javascript" src="criteria.js"></script>
  </head>
  <body onload="initWin(\'%(data-set)s\', \'%(modes)s\');">
    <div id="modal-back">
      <div id="filter-mod">
        <div id="filter-stat">
          <div id="stat-list">
          </div>
        </div>
        <div id="filter-criteria">
          <div id="filter-ctrl">
            <span id="crit-title"></span>
            <button id="filter-add-crit" onclick="filterAddCrit();">
              Add
            </button>
            <button id="filter-update-crit" onclick="filterUpdateCrit();">
              Update
            </button>
            <button id="filter-delete-crit" onclick="filterDeleteCrit();">
              Delete
            </button>
            <button id="filter-undo-crit" onclick="filterUndoCrit();">
              Undo
            </button>
            <button id="filter-redo-crit" onclick="filterRedoCrit();">
              Redo
            </button>
            <span id="close-filter" onclick="filterModOff();">&times;</span>
          </div>
          <div id="filter-cur-crit-text">
            <span id="crit-text"></span>
            <span id="crit-error"></span>
          </div>
          <div id="filter-cur-crit">
            <div id="cur-crit-numeric">
              <span id="crit-min" class="num-set"></span>
              <input id="crit-min-inp" class="num-inp"
                type="text" onchange="checkCurCrit(\'min\');"/>
              <span id="crit-sign" class="num-sign"
                onclick="checkCurCrit(\'sign\');"></span>
              <input id="crit-max-inp" class="num-inp"
                type="text" onchange="checkCurCrit(\'max\');"/>
              <span id="crit-max" class="num-set"></span>
              <span id="num-count" class="num-count"></span><br/>
              <input id="crit-undef-check" class="num-inp"
                type="checkbox"  onchange="checkCurCrit(\'undef\');"/>
              <span id="crit-undef-count" class="num-count"
                class="num-count"></span>
            </div>
            <div id="cur-crit-enum">
              <div id="wrap-crit-enum">
                <div id="wrap-crit-enum-list">
                  <div id="cur-crit-enum-list">
                     <div id="op-enum-list">
                     </div>
                  </div>
                </div>
                <div id="cur-crit-enum-mode">
                  <span id="crit-mode-and-span">
                    <input id="crit-mode-and" class="num-inp" type="checkbox"
                      onchange="checkCurCrit(\'mode-and\');"/>AND
                  </span><br/>
                  <span id="crit-mode-only-span">
                    <input id="crit-mode-only" class="num-inp" type="checkbox"
                      onchange="checkCurCrit(\'mode-only\');"/>ONLY
                  </span><br/>
                  <span id="crit-mode-not-span">
                    <input id="crit-mode-not" class="num-inp" type="checkbox"
                      onchange="checkCurCrit(\'mode-not\');"/>NOT
                  </span><br/>
                </div>
              </div>
            </div>
          </div>
          <div id="filter-list-criteria">
            <div id="crit-list">
            </div>
          </div>
        </div>
      </div>
    </div>
    <div id="top">
      <div id="top-left">
        <div id="data-sets">
          <select id="data_set" onchange="changeDataSet();">
            %(data-set-list)s
          </select>
          <button id="open-filter" onclick="filterModOn();">Filter</button>
          <span id="list-report"></span>
          <input id="list-rand-portion" type="number" min="1" max="5"
            onchange="listRandPortion();"/>
        </div>
        <div id="rec-list">
        </div>
      </div>
      <div id="top-right">
        <iframe id="record" name="record" src="norecords"></iframe>
      </div>
    </div>
  </body>
</html>''' % params

def emptyPage(output):
    print >> output, '''
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
  <head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
    <link rel="stylesheet" href="anf.css" type="text/css" media="all"/>
  </head>
  <body>
    <h3>No records available</h3>
  </body>
</html>'''