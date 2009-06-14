本文件还不是正式的帮助文件, 仅仅是那些非直观功能的简单说明列表.

Civ4 XML View v0.1.2
本程序设计目标为Sid Meier's Civilization中的XML文件, 主要用于浏览和发掘其中的数据, 编辑方面仅支持基本的修改.

额外功能说明
主窗口和书签窗口支持文件或目录的拖放
支持命令行参数的传递以打开文件或目录
若当前项目能被编辑, 按F2或双击鼠标可进入编辑状态, 书签的编辑只能通过F2启动
某些功能仅能通过右键菜单访问

正则表达式的语法类型说明
Regular expression: A rich Perl-like pattern matching syntax.
Wildcard: This provides a simple pattern matching syntax similar to that used by shells (command interpreters) for "file globbing".
Fixed string: The pattern is a fixed string.

设定文件说明
Civ4XML_settings.ini
[Path]
startup: 初始工作目录
dirRoot: 目录窗口根目录

[Filter]
deep: 设定过滤时搜索模式, false或true, 若设为true则相对较慢

设定文件中目录的分隔符为"/", 或使用了转义符的"\\", 使用"\"则无效. 例如
startup=c:/temp
startup=c:\\temp

