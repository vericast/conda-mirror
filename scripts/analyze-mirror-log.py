import argparse
import sys
from pprint import pprint, pformat
from collections import Counter, defaultdict


def split_log_file_on_date(log_file):
    grouped_lines = []
    dates = []
    lines = []
    num_lines = 0
    with open(log_file, 'r') as f:
        num_lines += 1
        lines = f.readlines()
    for line in lines:
        if "CST" in line:
            dates.append(line.strip())
            if lines:
                lines = []
                grouped_lines.append(lines)
        lines.append(line)
    print('num_lines', num_lines)
    return grouped_lines, dates


def analyze_block(lines):
    levels = {k: k[0] for k in ("DEBUG", "INFO", "WARNING", "ERROR")}
    groups = defaultdict(list) 
    line_prefix = [line.split(':', 1)[0] for line in lines]
    
    for pref, line in zip(line_prefix, lines):
        groups[levels.get(pref, 'O')].append(line)
        
    level_counts = Counter((levels.get(prefix, 'O') for prefix in line_prefix))

    return groups, level_counts


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("log_file", action="store", help="Path to the file to analyze")
    ap.add_argument("--line-type", action="append", default=[],
                    help=("Type of line to show. Options are "
                          "'D' for debug lines, "
                          "'I' for info lines, "
                          "'W' for warning lines, "
                          "'E' for error lines, "
                          "'O' for other lines, "))
    ap.add_argument("--run-number", action="store",
                    help="Show info for only the run indicated by run_number",
                    type=int)
    ap.add_argument("--show-last", action="store", help="Show this many previous runs", 
                    default=-50, type=int)
    args = ap.parse_args()
    print(args)

    blocks, dates = split_log_file_on_date(args.log_file)

    print('len(blocks)', len(blocks))
    output_fmt = "{line_num:<5} {relative_line_num:<3} {date} {num_lines:>6} {output}"
    def _show_output(line_num, relative_line_num, date, block):
        groups, counts = analyze_block(block)
        print(output_fmt.format(
            line_num=line_num, 
            relative_line_num=relative_line_num, 
            date=date, 
            num_lines=len(block),
            output=pformat(counts)))
        for k, v in groups.items():
            if k in args.line_type:
                print("\n\nShowing lines of type %s:" % k)
                pprint(v)

    if args.show_last > 0:
        args.show_last = -args.show_last
    show_last = args.show_last
    if args.run_number is not None:
        if args.run_number >= 0:
            line_num = args.run_number
            relative_line_num = line_num - len(dates)
        elif args.run_number < 0:
            relative_line_num = args.run_number
            line_num = len(dates) + relative_line_num
        date = dates[line_num]
        block = blocks[line_num]
        _show_output(line_num, relative_line_num, date, block)
        sys.exit(0)
    for line_num, (date, block) in enumerate(zip(dates[show_last:], blocks[show_last:])):
        relative_line_num = show_last + line_num
        line_num = show_last + len(dates)
        _show_output(line_num, relative_line_num, date, block)
