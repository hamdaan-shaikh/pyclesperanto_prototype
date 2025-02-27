def test_mode_box_2d():
    import pyclesperanto_prototype as cle

    image = cle.asarray([
        [0, 0, 0, 1, 1, 1],
        [0, 0, 0, 1, 1, 1],
        [0, 0, 0, 3, 1, 1],
        [0, 2, 2, 2, 1, 1],
        [0, 2, 2, 2, 1, 1],
        [0, 2, 2, 1, 1, 1],
    ])

    reference = cle.asarray([
        [0, 0, 0, 1, 1, 1],
        [0, 0, 0, 1, 1, 1],
        [0, 0, 0, 1, 1, 1],
        [0, 0, 2, 2, 1, 1],
        [0, 2, 2, 2, 1, 1],
        [0, 2, 2, 1, 1, 1],
    ])

    result = cle.mode_box(image)

    assert cle.array_equal(result, reference)

def test_mode_box_3d():
    import pyclesperanto_prototype as cle

    image = cle.asarray([[
        [0, 0, 0, 1, 1, 1],
        [0, 0, 0, 1, 1, 1],
        [0, 0, 0, 3, 1, 1],
        [0, 2, 2, 2, 1, 1],
        [0, 2, 2, 2, 1, 1],
        [0, 2, 2, 1, 1, 1],
    ]])

    reference = cle.asarray([[
        [0, 0, 0, 1, 1, 1],
        [0, 0, 0, 1, 1, 1],
        [0, 0, 0, 1, 1, 1],
        [0, 0, 2, 2, 1, 1],
        [0, 2, 2, 2, 1, 1],
        [0, 2, 2, 1, 1, 1],
    ]])

    result = cle.mode_box(image)

    assert cle.array_equal(result, reference)
