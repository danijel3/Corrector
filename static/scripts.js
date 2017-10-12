function update_norm(corp_name, item_id) {
    var value = $('#edit_text').val();
    $.post('/norm/' + corp_name + '/modify', {
        id: item_id,
        value: value
    });
    $('body').toggleClass('modified', true);
}

function revert_norm(corp_name, item_id) {
    if (!confirm('Czy na pewno?'))
        return;
    $.post('/norm/' + corp_name + '/revert', {
        id: item_id,
    });
    location.reload();
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