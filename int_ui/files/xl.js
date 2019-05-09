var sDSName = null;
var sTitlePrefix = null;
var sCommonTitle = null;
var sWsURL = null;

/*************************************/
function initXL(ds_name, common_title, ws_url) {
    sWsURL = ws_url;
    sDSName = ds_name; 
    document.getElementById("close-filter").style.display = "none";
    sFiltersH.init();
    sUnitsH.init("xl_filters", "xl_statunits", "ds=" + sDSName, true);
    sOpNumH.init();
    sOpEnumH.init();
    sViewH.init();
    sCreateWsH.init()
    if (sTitlePrefix == null) 
        sTitlePrefix = window.document.title;
    sCommonTitle = common_title;
    window.name = sCommonTitle + ":" + sDSName + ":R";
    document.title = sTitlePrefix + "/" + sDSName;
    document.getElementById("xl-name").innerHTML = sDSName;
    sUnitsH.setup();
}
    
/**************************************/
function wsCreate() {
    sCreateWsH.show();
}

function startWsCreate() {
    sCreateWsH.startIt();
}

/**************************************/
function onModalOff() {
}

function updateCurFilter(filter_name, force_it) {
}

function onFilterListChange() {
}

function openControlMenu() {
    sViewH.dropOn(document.getElementById("ds-control-menu"));
}

function goHome() {
    sViewH.dropOff();
    window.open('dir', sCommonTitle + ':dir');
}

function goToTree() {
    sViewH.dropOff();
    window.open("xl_tree?ds=" + sDSName, sCommonTitle + ":" + sDSName + ":L");
}

/*************************************/
function openNote() {
    sViewH.dropOff();
    loadNote();
    sViewH.modalOn(document.getElementById("note-back"));
}

function saveNote() {
    sViewH.dropOff();
    loadNote(document.getElementById("note-content").value);
    sViewH.modalOff();
}

function loadNote(content) {
    args = "ds=" + sDSName;
    if (content) 
        args += "&note=" + encodeURIComponent(content);        
    ajaxCall("dsnote", args, function(info) {
        document.getElementById("note-ds-name").innerHTML = info["name"];
        document.getElementById("note-content").value = info["note"];
        document.getElementById("note-time").innerHTML = 
            (info["time"] == null)? "" : "Modified at " + timeRepr(info["time"]);
    });
}

/*************************************/
function showExport() {
    sViewH.dropOff();
    if (sUnitsH.mExportFormed) {
        sViewH.dropOn(document.getElementById("ws-export-result"));
        return;
    }
    if (sUnitsH.mCount <= 300)
        res_content = 'Export ' + sUnitsH.mCount + ' records?<br>' +
            '<button class="drop" onclick="doExport();">Export</button>' + 
            '&emsp;<button class="drop" onclick="sViewH.dropOff();">Cancel</button>';
    else
        res_content = 'Too many records for export: ' + 
            sUnitsH.mCount + ' > 300.<br>' +
            '<button class="drop" onclick="sViewH.dropOff();">Cancel</button>';
    res_el = document.getElementById("ws-export-result");
    res_el.innerHTML = res_content;
    sViewH.dropOn(res_el);
}

function doExport() {
    args = "ds=" + sDSName + "&conditions=" + 
        encodeURIComponent(JSON.stringify(sConditionsH.getConditions()));
    ajaxCall("xl_export", args, setupExport);
}

function setupExport(info) {
    res_el = document.getElementById("ws-export-result");
    if (info["fname"]) {
        res_el.className = "drop";
        res_el.innerHTML = 'Exported ' + sUnitsH.mCount + ' records<br>' +
        '<a href="' + info["fname"] + '" target="blank" ' + 'download>Download</a>';
    } else {
        res_el.className = "drop problems";
        res_el.innerHTML = 'Bad configuration';
    }
    sUnitsH.mExportFormed = true;
    showExport();
}

/*************************************/
