

from django import template
register = template.Library()

def tablecols(data, cols):
    rows = []
    row = []
    index = 0
    for user in data:
        row.append(user)
        index = index + 1
        if index % cols == 0:
            rows.append(row)
            row = []
    # Still stuff missing?
    if len(row) > 0:
        rows.append(row)
    return rows
register.filter_function(tablecols)