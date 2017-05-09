


def dparse(*dstr):
    dint = [int(x) for x in dstr]

    if len(dint) == 2:
        # For months we want the last day of each month
        dint.append(calendar.monthrange(*dint)[1])
    if len(dint) == 1:
        # For annual we want the last day of the year
        dint.append(12)
        dint.append(calendar.monthrange(*dint)[1])

    return datetime.datetime(*dint)

# def dparse(yr, mo, dy, hr, minute, sec):
#     # Date parser for working with the date format from PRMS files
#
#     # Convert to integer first
#     yr, mo, dy, hr, minute, sec = [int(x) for x in [yr, mo, dy, hr, minute, sec]]
#
#     dt = datetime.datetime(yr, mo, dy, hr, minute, sec)
#     return dt