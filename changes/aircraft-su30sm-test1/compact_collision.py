"""Remove unreferenced collision vertices, preserving every physical triangle exactly."""
from pathlib import Path

def compact_collision(path):
    path = Path(path)
    lines = path.read_text().splitlines()
    first_face = lines.index('F')
    vertices = [s for s in lines[:first_face] if s.startswith('V ')]
    faces = lines[first_face:]
    used = sorted({int(i) for s in faces if s.startswith('V ') for i in s[2:].split()})
    mapping = {old: new for new, old in enumerate(used)}
    result = ['SURF'] + [vertices[i] for i in used]
    result += ['V ' + ' '.join(str(mapping[int(i)]) for i in s[2:].split()) if s.startswith('V ') else s for s in faces]
    # Compare the actual triangle corner coordinates, independent of indexing.
    before = [[vertices[int(i)] for i in s[2:].split()] for s in faces if s.startswith('V ')]
    after = [[result[1 + mapping[int(i)]] for i in s[2:].split()] for s in faces if s.startswith('V ')]
    assert before == after
    path.write_text('\n'.join(result) + '\n')
    return {'before_vertices': len(vertices), 'after_vertices': len(used), 'physical_faces': len(before), 'identical_physical_triangles': True}
