import os
import re
import csv
import glob
import shutil

def parse_log_file(file_path):
    """Parse a single ABC solver log file and extract relevant information."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract filename
    filename_match = re.search(r'File: ([^\n]+)', content)
    aig_file_path = filename_match.group(1).strip() if filename_match else None
    filename = os.path.basename(aig_file_path) if aig_file_path else os.path.basename(file_path)
    
    # Save the full AIG path for copying later
    full_aig_path = aig_file_path
    
    # Determine if property proved or bug found
    is_proved = "Property proved" in content
    is_bug = "was asserted in frame" in content or "Output 0 of miter" in content
    
    # Extract execution time
    time_match = re.search(r'Time =\s+(\d+\.\d+)', content)
    time = float(time_match.group(1)) if time_match else None
    
    # Extract status
    if is_proved:
        status = "PROVED"
    elif is_bug:
        status = "BUG"
    else:
        status = "UNKNOWN"
    
    # Extract frame information
    frame_info = "N/A"
    if is_bug:
        frame_match = re.search(r'asserted in frame (\d+)', content)
        if frame_match:
            frame_info = frame_match.group(1)
    elif is_proved:
        invariant_match = re.search(r'Invariant F\[(\d+)\]', content)
        if invariant_match:
            frame_info = invariant_match.group(1)
    
    # Extract more detailed statistics
    stats = {}
    stats_section = re.search(r'SAT solving =\s+(\d+\.\d+) sec \(\s*(\d+\.\d+) %\)[^}]*TOTAL\s+=\s+(\d+\.\d+) sec', content, re.DOTALL)
    if stats_section:
        stats['sat_solving_time'] = float(stats_section.group(1))
        stats['sat_solving_percent'] = float(stats_section.group(2))
        stats['total_time'] = float(stats_section.group(3))
    
    return {
        'filename': filename,
        'full_aig_path': full_aig_path,
        'status': status,
        'time': time,
        'frame': frame_info,
        **stats
    }

def main():
    # Create non-trivial cases directory if it doesn't exist
    non_trivial_dir = "non-trivial_cases"
    if not os.path.exists(non_trivial_dir):
        os.makedirs(non_trivial_dir)
    
    # Get all log files in the abc_solver_logs directory
    log_files = glob.glob('abc_solver_logs/*.txt')
    print(f"Found {len(log_files)} log files")
    
    results = []
    non_trivial_count = 0
    non_trivial_aig_files = []
    
    for log_file in log_files:
        try:
            log_data = parse_log_file(log_file)
            log_data['log_file'] = os.path.basename(log_file)
            results.append(log_data)
            
            # Check if this is a non-trivial case (total_time > 600 seconds)
            if log_data.get('total_time', 0) > 600:
                non_trivial_count += 1
                
                # Get the AIG file path
                aig_file_path = log_data.get('full_aig_path')
                if aig_file_path and os.path.exists(aig_file_path):
                    # Copy the AIG file to the non-trivial cases directory
                    aig_filename = os.path.basename(aig_file_path)
                    dest_file = os.path.join(non_trivial_dir, aig_filename)
                    shutil.copy2(aig_file_path, dest_file)
                    print(f"Copied non-trivial AIG case: {aig_file_path} -> {dest_file}")
                    non_trivial_aig_files.append(aig_filename)
                else:
                    print(f"Warning: Could not find AIG file for non-trivial case: {log_file}")
        except Exception as e:
            print(f"Error processing {log_file}: {str(e)}")
    
    # Write results to CSV
    csv_fields = ['log_file', 'filename', 'full_aig_path', 'status', 'time', 'frame', 
                 'sat_solving_time', 'sat_solving_percent', 'total_time']
    
    with open('abc_solver_results.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
        writer.writeheader()
        for result in results:
            writer.writerow({field: result.get(field, 'N/A') for field in csv_fields})
    
    print(f"Results written to abc_solver_results.csv")
    
    # Write non-trivial cases to a separate CSV
    with open('non_trivial_results.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
        writer.writeheader()
        for result in results:
            if result.get('total_time', 0) > 600:
                writer.writerow({field: result.get(field, 'N/A') for field in csv_fields})
    
    print(f"Non-trivial cases written to non_trivial_results.csv")
    
    # Write the list of non-trivial AIG files
    with open('non_trivial_aig_list.txt', 'w') as f:
        for aig_file in non_trivial_aig_files:
            f.write(f"{aig_file}\n")
    
    print(f"List of non-trivial AIG files written to non_trivial_aig_list.txt")
    
    # Print summary
    proved_count = sum(1 for r in results if r['status'] == 'PROVED')
    bug_count = sum(1 for r in results if r['status'] == 'BUG')
    unknown_count = sum(1 for r in results if r['status'] == 'UNKNOWN')
    
    print(f"Summary: {proved_count} proved, {bug_count} bugs, {unknown_count} unknown")
    print(f"Non-trivial cases (>600 seconds): {non_trivial_count}")
    print(f"Successfully copied non-trivial AIG files: {len(non_trivial_aig_files)}")

if __name__ == "__main__":
    main()
