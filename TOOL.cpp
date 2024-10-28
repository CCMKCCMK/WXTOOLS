#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>
#include <windows.h>

const size_t MAX_SIZE = 1024 * 1024 * 1024; // 1GB

std::string get_filename(const std::string& path) {
    size_t pos = path.find_last_of("\\/");
    return (pos == std::string::npos) ? path : path.substr(pos + 1);
}

std::string get_file_stem(const std::string& filename) {
    size_t pos = filename.find_last_of(".");
    return (pos == std::string::npos) ? filename : filename.substr(0, pos);
}

void create_directory(const std::string& path) {
    CreateDirectoryA(path.c_str(), NULL);
}

std::vector<std::string> list_files(const std::string& folder_path) {
    std::vector<std::string> files;
    WIN32_FIND_DATAA find_data;
    HANDLE find_handle = FindFirstFileA((folder_path + "\\*").c_str(), &find_data);

    if (find_handle != INVALID_HANDLE_VALUE) {
        do {
            if (!(find_data.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) {
                files.push_back(folder_path + "\\" + find_data.cFileName);
            }
        } while (FindNextFileA(find_handle, &find_data));
        FindClose(find_handle);
    }

    return files;
}

void cut(const std::string& file_path) {
    std::ifstream input(file_path, std::ios::binary);
    if (!input) {
        std::cerr << "Error opening input file." << std::endl;
        return;
    }

    std::string result_dir = "result";
    create_directory(result_dir);

    std::string base_name = get_file_stem(get_filename(file_path));
    std::string extension = file_path.substr(file_path.find_last_of('.'));
    size_t file_count = 0;
    std::vector<char> buffer(MAX_SIZE);

    while (input) {
        std::string output_name = result_dir + "\\" + base_name + extension + "._" + std::to_string(file_count++);
        std::ofstream output(output_name, std::ios::binary);

        input.read(buffer.data(), MAX_SIZE);
        std::streamsize bytes_read = input.gcount();
        output.write(buffer.data(), bytes_read);
    }

    std::cout << "File cut into " << file_count << " parts." << std::endl;
}

void collect(const std::string& folder_path) {
    std::vector<std::string> subfiles = list_files(folder_path);

    if (subfiles.empty()) {
        std::cerr << "No subfiles found in the specified folder." << std::endl;
        return;
    }

    std::sort(subfiles.begin(), subfiles.end());

    std::string base_name = get_file_stem(get_filename(subfiles[0]));
    base_name = base_name.substr(0, base_name.find_last_of('_'));
    std::ofstream output(base_name, std::ios::binary);

    for (const auto& subfile : subfiles) {
        std::ifstream input(subfile, std::ios::binary);
        output << input.rdbuf();
    }

    std::cout << "Original file rebuilt as '" << base_name << "'." << std::endl;
}

int main(int argc, char* argv[]) {
    if (argc != 3) {
        std::cerr << "Usage: " << argv[0] << " CUT/COLLECT file_path/folder_path" << std::endl;
        return 1;
    }

    std::string operation = argv[1];
    std::string path = argv[2];

    if (operation == "CUT") {
        cut(path);
    } else if (operation == "COLLECT") {
        collect(path);
    } else {
        std::cerr << "Invalid operation. Use CUT or COLLECT." << std::endl;
        return 1;
    }

    return 0;
}