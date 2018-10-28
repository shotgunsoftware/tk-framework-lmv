import base64
import os
import shutil
import subprocess
import tempfile


class AliasTranslator(object):
    def __init__(self, path, resources_dir, svf_path=None):
        self.path = path
        self.resources_dir = resources_dir
        self.svf_path = svf_path

    def translate(self):
        # Get translator
        translator = os.path.join(self.resources_dir, "LMVExtractor", "atf_lmv_extractor.exe")

        # Temporal dir
        tmpdir = tempfile.mkdtemp(prefix='lmv_')

        # File name
        file_name = os.path.basename(self.path)

        # JSON file
        index_path = os.path.join(tmpdir, 'index.json')
        with open(index_path, 'w') as _:
            pass

        # Copy source file locally
        source_path_temporal = os.path.join(tmpdir, file_name)
        shutil.copyfile(self.path, source_path_temporal)

        # Execute translation command
        command = [translator, index_path, source_path_temporal]
        command_line_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process_output, _ = command_line_process.communicate()

        if command_line_process.returncode != 0:
            raise Exception(process_output)

        return tmpdir
    
    def _get_svf_thumbnail(self):
        # Get translator
        translator = os.path.join(self.resources_dir, "SVFThumbnailExtractor", "svf_thumb.exe")
        
        # File name
        file_name = os.path.splitext(os.path.basename(self.svf_path))[0]
        
        # Tmpdir
        tmpdir = os.path.dirname(os.path.dirname(os.path.dirname(self.svf_path)))
        
        images_tmp_path = os.path.join(tmpdir, 'images_{}'.format(file_name))
        
        if not os.path.exists(images_tmp_path):
            os.makedirs(images_tmp_path)

        # Execute translation command
        command = [translator, self.svf_path, '-outpath=' + images_tmp_path, '-size=2560', '-depth=4']
        command_line_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        process_output, _ = command_line_process.communicate()

        if command_line_process.returncode != 0:
            raise Exception(process_output)
        
        images_file_path = os.path.join(images_tmp_path, '01_thumb_2560x2560.png')
        
        with open(images_file_path, "rb") as fh:
            data = fh.read()

        return data

    def get_thumbnail_data(self):
        if os.path.splitext(self.path)[1][1:] != "wire":
            return self._get_svf_thumbnail()
        else:
            with open(self.path) as src_file:
                line = src_file.readline()
    
                while line != "thumbnail JPEG\n":
                    line = src_file.readline()
    
                line = src_file.readline()
    
                data = []
                while line != "thumbnail end\n":
                    data.append(line.replace('Th ', ''))
                    line = src_file.readline()
    
                return base64.b64decode(''.join(data))
