import sys
import os
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton, QFileDialog
from PyQt5.QtCore import Qt
import multiprocessing
import argparse

class tool():
    MAX_SIZE = 1024 * 1024 * 1024  # 1GB

    def __init__(self):
        pass

    def get_filename(self, path):
        return os.path.basename(path)

    def get_file_stem(self, filename):
        return os.path.splitext(filename)[0]

    def create_directory(self, path):
        os.makedirs(path, exist_ok=True)

    def list_files(self, folder_path):
        try:
            files = [
                os.path.join(folder_path, f)
                for f in os.listdir(folder_path)
                if os.path.isfile(os.path.join(folder_path, f))
            ]
            return sorted(files)
        except Exception as e:
            print(f"Error listing files in {folder_path}: {e}")
            return []
    
    @staticmethod
    def write_chunk(chunk, output_name):
        with open(output_name, 'wb') as output_file:
            output_file.write(chunk)
        print(f"Created chunk: {output_name}")

    def cut(self, file_path, max_size=MAX_SIZE):
        """
        Splits a file into smaller parts of specified maximum size.
        Args:
            file_path (str): The path to the file to be split.
            max_size (int, optional): The maximum size of each part in bytes. Defaults to MAX_SIZE.
        Returns:
            None
        Raises:
            Exception: If an error occurs during the file splitting process.
        Notes:
            - The resulting parts are saved in a directory named after the original file with a "_parts" suffix.
            - Each part is named using the original file's base name and extension, followed by an incrementing index.
            - If the file is successfully split, a message indicating the number of parts is printed.
            - If an error occurs, an error message is printed.
        Example:
            If the file is successfully split into 1 part, the message "File cut into 1 parts." is printed, but the folder may be empty if the writing process fails.
        """
        if not os.path.isfile(file_path):
            print("Error: Input path is not a file.")
            return

        result_dir = f"{file_path}_parts"
        self.create_directory(result_dir)

        base_name = self.get_file_stem(self.get_filename(file_path))
        extension = os.path.splitext(file_path)[1]

        file_count = 0
        buffer_size = max_size

        try:
            with open(file_path, 'rb') as input_file:
                pool = multiprocessing.Pool()
                while True:
                    chunk = input_file.read(buffer_size)
                    if not chunk:
                        break
                    output_name = os.path.join(
                        result_dir,
                        f"{base_name}{extension}._{file_count}"
                    )
                    pool.apply_async(self.write_chunk, (chunk, output_name))
                    file_count += 1

                pool.close()
                pool.join()

            print(f"File cut into {file_count} parts.")
        except Exception as e:
            print(f"Error during cutting: {e}")

    def collect(self, folder_path):
        subfiles = self.list_files(folder_path)

        if not subfiles:
            print("No subfiles found in the specified folder.")
            return

        subfiles = [f for f in subfiles if f.rsplit('.', 1)[-1].startswith('_')]

        if not subfiles:
            print("No valid subfiles found in the specified folder.")
            return

        subfiles.sort()

        # group based on file name
        subfiles_grouped = {}
        for subfile in subfiles:
            base_name = self.get_file_stem(self.get_filename(subfile))
            if base_name not in subfiles_grouped:
                subfiles_grouped[base_name] = []
            subfiles_grouped[base_name].append(subfile)
                
        for subfiles in subfiles_grouped.values():
            # get base name
            base_name_with_extension = self.get_filename(subfiles[0])
            base_name = self.get_file_stem(base_name_with_extension)
            base_name = base_name.rsplit('_', 1)[0]
            output_file_path = os.path.join(folder_path, base_name)

            try:
                with open(output_file_path, 'wb') as output_file:
                    for subfile in subfiles:
                        with open(subfile, 'rb') as input_file:
                            output_file.write(input_file.read())
                        print(f"Added {subfile} to {output_file_path}")

                print(f"Original file rebuilt as '{output_file_path}'.")

                # delete subfiles
                for subfile in subfiles:
                    os.remove(subfile)
                    print(f"Deleted {subfile}")
            except Exception as e:
                print(f"Error during collecting: {e}")
                
class Window(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("文件切割工具")
        self.setGeometry(100, 100, 400, 200)
        self.setLayout(QVBoxLayout())

        self.cut_button = QPushButton("切割文件")
        self.cut_button.clicked.connect(self.cut_file)
        self.layout().addWidget(self.cut_button)

        self.collect_button = QPushButton("合并文件")
        self.collect_button.clicked.connect(self.collect_files)
        self.layout().addWidget(self.collect_button)

        self.result_label = QLabel("拖放文件到此处以切割；拖放文件夹到此处以合并；或使用按钮。")
        self.layout().addWidget(self.result_label)

        self.setAcceptDrops(True)

    def cut_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择要切割的文件",
            "",
            "所有文件 (*)"
        )

        if not file_path:
            self.result_label.setText("未选择文件。")
            return

        tool_instance = tool()
        tool_instance.cut(file_path)
        self.result_label.setText("文件切割成功。")

    def collect_files(self):
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "选择包含文件部分的文件夹"
        )

        if not folder_path:
            self.result_label.setText("未选择文件夹。")
            return

        tool_instance = tool()
        tool_instance.collect(folder_path)
        self.result_label.setText("文件合并成功。")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if os.path.isfile(file_path):
                self.handle_file_drop(file_path)
            elif os.path.isdir(file_path):
                self.handle_folder_drop(file_path)

    def handle_file_drop(self, file_path):
        tool_instance = tool()
        tool_instance.cut(file_path)
        self.result_label.setText("文件通过拖放切割成功。")

    def handle_folder_drop(self, folder_path):
        tool_instance = tool()
        tool_instance.collect(folder_path)
        self.result_label.setText("文件通过拖放合并成功。")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Window()
    window.show()
    sys.exit(app.exec_())
