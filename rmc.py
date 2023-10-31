import os
import glob
import re
import datetime
from tqdm import tqdm
import json


def remove_head_and_tail_double_quotations(arg: str):
    """
    最初と最後のダブルクオーテーションであれば、取り除いて返す。
    (右クリックで、「パスのコピー」で渡されたターゲットのディレクトリをパースするため)
    """
    assert type(arg) == str
    if (len(arg) > 0) and arg[0] == '"':
        arg = arg[1:]

    if (len(arg) > 0) and arg[-1] == '"':
        arg = arg[:-1]

    return arg


def obtain_pattern(targets: list):
    """
    正規表現で使う pattern を返す関数。
    python コードで、# コメント を削除するために使う想定。
    """
    pattern = [r' *# *' + target + '.*?\n' for target in targets]
    return '|'.join(pattern)


def remove_comment_of_python(src: str, dst: str, targets=[], rm_docstring=True):
    """
    dst が None の場合は、書き換えを実行せず、中身を確認する。

    Parameters
    ----------
    src : str
        コメント削除したい .py ファイル
    dst : str
        コメント削除後の .py ファイルの保存先。
    target : list (of str)
        削除したいコメントの先頭に含まれる文字列。(Ex. 'TODO:', 'FIXME:')
        なお、'' (空文字) を指定した場合、# で始まるすべてのコメントが除去される。
    rm_docstring : bool (default : True)
        関数の docstring を除去するかどうか。
    """
    # [START] check args
    assert os.path.exists(src) and os.path.isfile(src) and (os.path.splitext(src)[-1] == '.py')
    assert os.path.splitext(dst)[-1] == '.py'
    assert src != dst  # INFO: 231031 上書き防止
    # [END] check args
        
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    
    f_src = open(src, 'r', encoding='utf-8')
    f_dst = open(dst, 'a', encoding='utf-8')

    is_docstring = False
    pattern = obtain_pattern(targets)    
    for text in f_src:
        if (rm_docstring == True) and (('"""' in text) or ("'''" in text)):
            text = ''
            is_docstring = not is_docstring

        if is_docstring == False:
            if len(targets) > 0:
                match_list = re.findall(pattern, text)
                assert len(match_list) in [0, 1]
                if len(match_list) == 1:
                    text = text.replace(match_list[0][:-1], '')  # INFO: 231031 [:-1] は、末尾の改行コードを落とすため。  # FIXME: \n でない場合を想定すること。
            f_dst.write(text)

    f_src.close()
    f_dst.close()


def main(src: str, targets: list, rm_docstring: bool, *, dst_folder_name='dst'):
    src_dir = remove_head_and_tail_double_quotations(src)

    if os.path.isdir(src_dir):  # TODO: 231031 現状はディレクトリ配下のみだが、単体ファイルでも実行できるといいかも？
        now = datetime.datetime.strftime(datetime.datetime.now(), '%y%m%d_%H%M%S')
        dst_dir = os.path.dirname(src_dir) + r'\{}_{}'.format(dst_folder_name, now)
        flist = glob.glob('{}/**/*.py'.format(src_dir), recursive=True)

        for src_path in tqdm(flist):
            dst_path = src_path.replace(src_dir, dst_dir)
            remove_comment_of_python(src=src_path, dst=dst_path, targets=targets, rm_docstring=rm_docstring)


if __name__ == '__main__':
    print('コメント削除したいフルパスのディレクトリを指定してください。')
    src = input('> ')
    assert os.path.exists(src)

    print('削除したいレベルを指定してください。')
    print('1: TODO:, FIXME:, EDIT: のみ')
    print('2: + INFO, [START], [END]')
    print('3: + docscting')
    print('4: + コメント全て (暴発多いので注意せよ)')
    level = input('> ')

    with open('config.json', 'r') as f:
        config = json.load(f)

    kwargs = config[level]
    main(src=src, **kwargs)