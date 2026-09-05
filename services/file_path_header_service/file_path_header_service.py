r"""Puts each converted file's own path at the top of it.

The embedder makes one vector per file out of the file's text, and that text
never mentioned where the file lives. So a note at

    Java\Spring Boot\Spring Security\Spring Security.md

was only findable by what was written inside it - searching "spring security"
missed it unless the words happened to appear in the body. Writing the path in
as the first line puts the folders and the file name into the vector, so the
place a note is filed counts towards finding it.

Written into the converted copy, never the download: the sources under the
input folder stay exactly as Drive gave them, which is what the reading pane
shows and what makes a re-run repeatable. Both conversion paths copy the
source over the top before calling this, so a second run restamps a clean file
rather than stacking a second header on the first.

Only the extensions the embedder reads are stamped - a .pdf sitting in the
folder is never embedded, so a header in it would be a change with no reader.
"""

import logging
from pathlib import Path

from services.file_embedder_service.file_embedder_service import FileEmbedderService

logger = logging.getLogger(__name__)


class FilePathHeaderService:

    #: The path, then a blank line, then the file as it was. A blank line so
    #: the header cannot run into a first paragraph and read as one sentence.
    HEADER_TEMPLATE = "{document_id}\n\n"

    def add_to_folder(self, converted_dir):
        """Stamps every embeddable file under `converted_dir`.

        Returns how many files were stamped.
        """
        converted_dir = Path(converted_dir)
        logger.info(f"Writing file paths into {converted_dir}")
        stamped_file_count = 0
        for file_path in sorted(converted_dir.rglob("*")):
            if file_path.is_file() and self.add_to_file(file_path, converted_dir):
                stamped_file_count += 1
        logger.info(f"Done. Wrote the path into {stamped_file_count} file(s)")
        return stamped_file_count

    def add_to_file(self, converted_file_path, converted_dir):
        """Stamps one converted file. False when there was nothing to do.

        False rather than an exception for a file that cannot be read: one bad
        file must not lose the rest of a run, and a file with no header is
        still embedded, just without its path counting towards a match.
        """
        converted_file_path = Path(converted_file_path)
        if converted_file_path.suffix.lower() not in FileEmbedderService.TEXT_EXTENSIONS:
            return False

        try:
            document_id = str(converted_file_path.relative_to(Path(converted_dir)))
        except ValueError:
            logger.warning(f"Not stamping {converted_file_path} - outside {converted_dir}")
            return False

        try:
            text = converted_file_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            logger.warning(f"Could not read {converted_file_path} - {error}")
            return False

        # Belt and braces: the callers copy the source over the top first, so
        # this should never fire - but stamping twice would be silent.
        if text.startswith(document_id):
            logger.debug(f"Already stamped: {converted_file_path}")
            return False

        try:
            converted_file_path.write_text(
                FilePathHeaderService.HEADER_TEMPLATE.format(document_id=document_id) + text,
                encoding="utf-8",
            )
        except OSError as error:
            logger.warning(f"Could not write {converted_file_path} - {error}")
            return False

        return True
