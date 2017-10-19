var norm_to_update = false;

function update_norm(corp_name, item_id) {
    $('#save_info').html('<span class="glyphicon glyphicon-refresh blue" aria-hidden="true"></span> Zapisuję...');
    if (norm_to_update)
        return;
    norm_to_update = true;
    setTimeout(function () {
        update_norm_call(corp_name, item_id);
    }, 1000);
}

function update_norm_call(corp_name, item_id) {
    $('#save_info').html('<span class="glyphicon glyphicon-refresh blue" aria-hidden="true"></span> Zapisuję...');
    norm_to_update = false;
    var value = $('#edit_text').val();
    $.post('/norm/' + corp_name + '/modify', {
        id: item_id,
        value: value
    }).done(function () {
        $('body').toggleClass('modified', true);
        $('#save_info').html('<span class="glyphicon glyphicon-ok green" aria-hidden="true"></span> Zapisałem!');
    }).fail(function () {
        $('#save_info').html('<span class="glyphicon glyphicon-remove red" aria-hidden="true"></span> Bład zapisywania!');
        norm_to_update = true;
    }).always(function () {
        if (norm_to_update)
            setTimeout(function () {
                update_norm_call(corp_name, item_id);
            }, 1000);
    });
}

function revert_norm(corp_name, item_id) {
    if (!confirm('Czy na pewno?'))
        return;
    $.post('/norm/' + corp_name + '/revert', {
        id: item_id,
    });
    location.reload();
}

function show_saved(corp_name, item_id) {
    $.get('/norm/' + corp_name + '/saved/' + item_id, function (text) {
        $('#savedContent').html(text);
        $('#savedDialog').modal();
    });
}

function norm_page(corp_name, page) {
    window.location.href = '/norm/' + corp_name + '/' + page;
}


function update_lex(corp_name, item_id, ph_idx, el) {
    var value = el.value;
    $.post('/lex/' + corp_name + '/modify', {
        id: item_id,
        index: ph_idx,
        value: value
    });
    el.parentNode.parentNode.className = 'warning';
}

function add_lex(corp_name, item_id) {
    $.post('/lex/' + corp_name + '/add', {
        id: item_id
    });
    location.reload();
}

function rem_lex(corp_name, item_id, ph_idx) {
    $.post('/lex/' + corp_name + '/rem', {
        id: item_id,
        index: ph_idx
    });
    location.reload();
}

function diff_norm() {

    $('#diff_btn').text('Edit');
    $('#diff_btn').off('click');
    $('#diff_btn').click(function () {
        edit_norm();
    });

    var norm = $('.norm .edit').text();
    var corr = $('.corr .edit').val();

    if (!norm || !corr) return;

    var diff = JsDiff.diffChars(norm, corr);

    norm = '';
    corr = '';
    for (i = 0; i < diff.length; i++) {
        if (diff[i].added) {
            corr += '<d>' + diff[i].value + '</d>';
        } else if (diff[i].removed) {
            norm += '<d>' + diff[i].value + '</d>';
        } else {
            corr += diff[i].value;
            norm += diff[i].value;
        }
    }

    $('.norm .diff').html(norm);
    $('.corr .diff').html(corr);


    $('.norm_item .edit').each(function () {
        $(this).toggleClass('hide', true);
    });

    $('.norm_item .diff').each(function () {
        $(this).toggleClass('hide', false);
    });
}

function edit_norm() {
    $('#diff_btn').text('Diff');
    $('#diff_btn').off('click');
    $('#diff_btn').click(function () {
        diff_norm();
    });

    $('.norm_item .edit').each(function () {
        $(this).toggleClass('hide', false);
    });

    $('.norm_item .diff').each(function () {
        $(this).toggleClass('hide', true);
    });
}