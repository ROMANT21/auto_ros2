from setuptools import find_packages, setup

package_name = "navigator"
navigator_node_name = "navigator_node"
navigation_bringup_node_name = "navigation_bringup_node"
utm_conversion_node_name = "utm_conversion_node"


_ = setup(
    name=package_name,
    version="1.0.0",
    python_requires=">=3.10",
    tests_require=["pytest"],
    packages=find_packages(exclude=["test"]),
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        #
        # note: please put a new entry in this array for each node in the pkg
        ("share/" + package_name, ["package.xml"]),
        ("share/" + navigator_node_name, ["package.xml"]),
        ("share/" + navigation_bringup_node_name, ["package.xml"]),
        ("share/" + utm_conversion_node_name, ["package.xml"]),
    ],
    zip_safe=True,
    maintainer="brendan",
    maintainer_email="bford@axmilius.com",
    description="TODO",
    license="TODO",
    entry_points={
        "console_scripts": [
            "navigator_node = navigator_node.main:main",
            "navigation_bringup_node = navigation_bringup_node.main:main",
            f"{utm_conversion_node_name} = {utm_conversion_node_name}.main:main",
        ],
    },
)
