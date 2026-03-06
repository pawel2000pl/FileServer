"use strict";

const unicode_arrow_up = String.fromCharCode(11105);
const unicode_arrow_down = String.fromCharCode(11107);
const unicode_search = String.fromCharCode(9000);
const unicode_search_action = String.fromCharCode(9205);

const auto_search_limit = 256;

function makeDynamicTable(table) {
    const tbody = table.querySelector('tbody');
    const headers = Array.from(table.querySelectorAll('thead tr th'));
    const all_rows = Array.from(table.querySelectorAll('tbody tr'));
    table.search_edits = Array();
    const tableId = 'table-filters:' + location.pathname + '??' + table.id;

    all_rows.forEach(tr => tr.visible = true);

    const refreshRows = () => {
        all_rows.forEach(row => {
            row.remove();
            if (row.visible)
                tbody.appendChild(row);
        });
    };

    const sortRows = (column, reverse) => {
        localStorage.setItem(tableId, JSON.stringify({column, reverse}));
        all_rows.sort((ea, eb) => {
            const ca = ea.children[column];
            const cb = eb.children[column];
            let a = 'sortkey' in ca.attributes ? ca.attributes.sortkey.value : ca.textContent;
            let b = 'sortkey' in cb.attributes ? cb.attributes.sortkey.value : cb.textContent;
            const inv = reverse ? -1 : 1;
            const numa = Number(a);
            const numb = Number(b);
            if (!isNaN(numa) && !isNaN(numb)) {
                return (numa - numb) * inv;
            }
            return a.localeCompare(b) * inv;
        });
        refreshRows();
    };

    const filterRows = () => {
        const filters = headers.map(th => {
            if (th.search_active === 0) return (_1, _2) => true;
            if (th.search_mode == 0) return (content, key) => content.startsWith(key);
            if (th.search_mode == 1) return (content, key) => content.match(key) !== null;
            if (th.search_mode == 2) return (content, key) => content === key;
            if (th.search_mode == 3) return (content, key) => content.localeCompare(key) < 0;
            if (th.search_mode == 4) return (content, key) => content.localeCompare(key) <= 0;
            if (th.search_mode == 5) return (content, key) => content.localeCompare(key) > 0;
            if (th.search_mode == 6) return (content, key) => content.localeCompare(key) >= 0;
            if (th.search_mode == 7) return (content, key) => content !== key;
            if (th.search_mode == 8) return (content, key) => content.match(key) === null;
            return (_1, _2) => true;
        });
        const values = table.search_edits.map(x => x.value);
        let indices = Array();
        for (let i=0;i<filters.length;i++)
            if (headers[i].is_dynamic && headers[i].search_active)
                indices.push(i);
        all_rows.forEach(tr => {
            tr.visible = true;
            indices.forEach(i => {
                if (!filters[i](tr.children[i].textContent, values[i])) {
                    tr.visible = false;
                }
            });
        });
        refreshRows();
    };

    headers.forEach((th, index) => {
        th.is_dynamic = false;
        if (!th.classList.contains('dynamic')) return;
        th.is_dynamic = true;
        const span_content = document.createElement('span');
        const span_options = document.createElement('span');
        const span_first_line = document.createElement('span');
        const input_search = document.createElement('input');
        const span_input_search = document.createElement('span');
        const span_action_search = document.createElement('span');
        const span_second_line = document.createElement('span');
        const children = Array.from(th.childNodes);
        children.forEach(c => c.remove());
        children.forEach(c => span_content.appendChild(c));
        table.search_edits[index] = input_search;
        input_search.onkeydown = (event) => {
            if (event.key === 'Enter') 
                filterRows();
        };
        input_search.oninput = () => {
            if (all_rows.length <= auto_search_limit)
                filterRows();
        }
        input_search.onchange = () => {
            if (all_rows.length <= auto_search_limit)
                filterRows();
        }
        span_action_search.onclick = filterRows;
        span_action_search.textContent = unicode_search_action;
        span_action_search.title = 'Filter';
        span_action_search.style.cursor = 'pointer';
        span_action_search.style.marginLeft = '8px'; 
        span_input_search.appendChild(input_search);
        span_input_search.appendChild(span_action_search);

        const sort_up_span = document.createElement('span');
        sort_up_span.textContent = unicode_arrow_up;
        sort_up_span.onclick = () => sortRows(index, false);
        sort_up_span.title = 'Sort ascending';
        sort_up_span.style.marginLeft = '8px';
        sort_up_span.style.cursor = 'pointer';
        span_options.appendChild(sort_up_span);

        const sort_down_span = document.createElement('span');
        sort_down_span.textContent = unicode_arrow_down;
        sort_down_span.onclick = () => sortRows(index, true);
        sort_down_span.title = 'Sort descending';
        sort_down_span.style.marginLeft = '8px';
        sort_down_span.style.cursor = 'pointer';
        span_options.appendChild(sort_down_span);

        const search_span = document.createElement('span');
        search_span.style.cursor = 'pointer';
        search_span.textContent = unicode_search;
        search_span.title = 'Filters';
        search_span.onclick = () => {
            if (span_second_line.style.display == 'none') {
                span_second_line.style.display = 'flex';
                th.search_active = 1;
            } else {
                span_second_line.style.display = 'none';
                all_rows.forEach(tr => tr.visible = true);
                refreshRows();
                th.search_active = 0;
            }
        };
        search_span.style.marginLeft = '8px';
        span_options.appendChild(search_span);

        const search_mode_span = document.createElement('span');
        th.search_mode = 0;
        search_mode_span.textContent = String.fromCharCode(8838);
        search_mode_span.title = 'starts with';
        search_mode_span.onclick = () => {
            th.search_mode = (th.search_mode + 1) % 9;
            if (th.search_mode == 0) {
                search_mode_span.textContent = String.fromCharCode(8838);
                search_mode_span.title = 'starts with';
            }
            if (th.search_mode == 1) {
                search_mode_span.textContent = String.fromCharCode(8834);
                search_mode_span.title = 'contains';
            }
            if (th.search_mode == 2) {
                search_mode_span.textContent = '=';
                search_mode_span.title = 'is equal';
            }
            if (th.search_mode == 3) {
                search_mode_span.textContent = '<';
                search_mode_span.title = 'is less';
            }
            if (th.search_mode == 4) {
                search_mode_span.textContent = String.fromCharCode(8804);
                search_mode_span.title = 'is less or equal';
            }
            if (th.search_mode == 5) {
                search_mode_span.textContent = '>';
                search_mode_span.title = 'is greater than';
            }
            if (th.search_mode == 6) {
                search_mode_span.textContent = String.fromCharCode(8805);
                search_mode_span.title = 'is greater or equal';
            }
            if (th.search_mode == 7) {
                search_mode_span.textContent = String.fromCharCode(8800);
                search_mode_span.title = 'is not equal';
            }
            if (th.search_mode == 8) {
                search_mode_span.textContent = String.fromCharCode(8836);
                search_mode_span.title = 'does not contain';
            }  
        };
        search_mode_span.style.marginLeft = '8px';
        search_mode_span.style.cursor = 'pointer';
        search_mode_span.style.width = '1em';
        span_second_line.appendChild(search_mode_span);

        span_first_line.style.display = 'flex';
        span_first_line.style.justifyContent = 'space-between';
        span_second_line.style.display = 'none';
        span_second_line.style.justifyContent = 'space-between';
        span_first_line.appendChild(span_content);
        span_first_line.appendChild(span_options);
        span_second_line.appendChild(span_input_search);
        span_second_line.appendChild(search_mode_span);
        th.appendChild(span_first_line);
        th.appendChild(span_second_line);
    });

    
    const lastSortStr = localStorage.getItem(tableId);
    if (lastSortStr !== null) {
        const lastSort = JSON.parse(lastSortStr);
        sortRows(lastSort.column, lastSort.reverse);
    }
}


Array.from(document.getElementsByClassName('dynamic-table')).forEach(makeDynamicTable);
