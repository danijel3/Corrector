var wavesurfer;

function create_wavesurfer(file) {
    wavesurfer = WaveSurfer.create({
        container: '#waveform',
        waveColor: 'green',
        progressColor: 'blue',
        normalize: true,
        height: 256,
        loopSelection: false,
        plugins: [
            WaveSurfer.regions.create({
                dragSelection: false,
                slop: 5
            }),
            WaveSurfer.minimap.create()
        ]
    });
    wavesurfer.load(file);
    document.onkeypress = function (e) {
        switch (e.which) {
            case 48:
                e.preventDefault();
                wavesurfer.playPause();
                break;
            case 43:
                e.preventDefault();
                zoom(1);
                break;
            case 45:
                e.preventDefault();
                zoom(-1);
                break;
            case 47:
                e.preventDefault();
                zoom(0);
                break;
            case 52:
                e.preventDefault();
                wavesurfer.skipBackward(1);
                break;
            case 54:
                e.preventDefault();
                wavesurfer.skipForward(1);
                break;
            case 49:
                e.preventDefault();
                wavesurfer.seekTo(0);
                break;
        }

    }
}

var regions = [];
var region_modified = false;

var zoom_levels = Array(0, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5);
var curr_zoom = 0;

function zoom(dir) {
    if (dir < 0) {
        curr_zoom--;
        if (curr_zoom < 0)
            curr_zoom = 0;
    } else if (dir > 0) {
        curr_zoom++;
        if (curr_zoom >= zoom_levels.length)
            curr_zoom = zoom_levels.length - 1;
    } else {
        curr_zoom = 0;
    }
    $('#zoom_level').html(zoom_levels[curr_zoom]);
    wavesurfer.zoom(100 * zoom_levels[curr_zoom]);
}

function add_region_curr() {
    var c = wavesurfer.getCurrentTime();
    add_region(c, c + 1);
}

function add_region(start, end) {

    var reg = wavesurfer.addRegion({
        start: start, // time in seconds
        end: end, // time in seconds
        color: 'rgba(255, 0, 0, 0.5)'
    });

    reg.on('dblclick', function () {
        reg.remove();
        var idx = regions.indexOf(reg);
        regions.splice(idx, 1);
    });

    reg.on('in', function () {
        wavesurfer.play(reg.end);
    });

    reg.on('update', function () {
        region_modified = true;
    });

    regions.push(reg);
    region_modified = true;
}


function save_regions(corp_name, item_id) {

    regs = [];
    rege = [];

    for (var i = 0; i < regions.length; i++) {
        regs.push(regions[i].start);
        rege.push(regions[i].end);
    }

    console.log(regs);

    $.post('/speech/' + corp_name + '/regions', {
        id: item_id,
        reg_start: regs,
        reg_end: rege
    });

    region_modified = false;
}

function diff_norm() {

    $('#diff_btn').text('Edit');
    $('#diff_btn').off('click');
    $('#diff_btn').click(function () {
        edit_norm();
    });

    var orig = $('#orig').text();
    var corr = $('#corr').val();

    if (!orig || !corr) return;

    var diff = JsDiff.diffChars(orig, corr);

    orig = '';
    corr = '';
    for (i = 0; i < diff.length; i++) {
        if (diff[i].added) {
            corr += '<d>' + diff[i].value + '</d>';
        } else if (diff[i].removed) {
            orig += '<d>' + diff[i].value + '</d>';
        } else {
            corr += diff[i].value;
            orig += diff[i].value;
        }
    }

    $('#orig_diff').html(orig);
    $('#corr_diff').html(corr);

    $('#orig').toggleClass('hide', true);
    $('#corr').toggleClass('hide', true);
    $('#orig_diff').toggleClass('hide', false);
    $('#corr_diff').toggleClass('hide', false);
}

function edit_norm() {
    $('#diff_btn').text('Diff');
    $('#diff_btn').off('click');
    $('#diff_btn').click(function () {
        diff_norm();
    });

    $('#orig').toggleClass('hide', false);
    $('#corr').toggleClass('hide', false);
    $('#orig_diff').toggleClass('hide', true);
    $('#corr_diff').toggleClass('hide', true);
}

var speech_modified = false;

function save_speech(corp_name, item_id) {
    var value = $('#corr').val();
    $.post('/speech/' + corp_name + '/modify', {
        id: item_id,
        value: value
    });
    $('#corr').toggleClass('modified', true);
    speech_modified = false;
}

function undo_speech(corp_name, item_id) {
    if (!confirm('Czy na pewno?'))
        return;
    $.post('/speech/' + corp_name + '/modify', {
        id: item_id,
        undo: true
    });
    location.reload();
}

function update_speech() {
    $('#corr').toggleClass('modified', true);
    speech_modified = true;
}

window.onbeforeunload = function () {
    if (region_modified)
        return 'Nie zapisano zmian w obszarach! Czy na pewno chcesz opuścić stronę?';
    if (speech_modified)
        return 'Nie zapisano zmian w transkrypcji! Czy na pewno chcesz opuścić stronę?';
    return null;
};