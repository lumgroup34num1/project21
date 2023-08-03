import hashlib,time


class Branch_ndoe:                                  #分支结点
    def __init__(self):
        self.type = 'branch'                        #十六进制编码的16种字符
        self.children = {'0': None, '1': None, '2': None, '3': None, '4': None, '5': None, '6': None, '7': None, '8': None, '9': None,
                         'a': None, 'b': None, 'c': None, 'd': None, 'e': None, 'f': None, 'value': False}


class Extension_node:                               #拓展结点类
    def __init__(self):
        self.type = 'extension'
        self.key = None
        self.value = Branch_ndoe()                  #将分支节点作为拓展节点的组成元素
        self.prefix = None                          #prefix
        self.node_hash = None                       #key-end
        self.node_value = None                      #value


class Leaf_node:                                    #叶子结点
    def __init__(self):
        self.type = 'leaf'
        self.key_end = None
        self.value = None
        self.prefix = None                         #prefix
        self.node_value = None                     #key-end
        self.node_hash = None                      #value


class Tree:                                        #MPT树类
    def __init__(self,tree=None):
        if tree != None:
            self.root = tree
        else:
            self.root= self.make_extension()
            self.root.prefix = 'root'              #默认root作为根节点prefix
            self.value = None
            self.hash = None


    def add_node(self,node,key,value):
        if node.prefix == 'root':
            if self.root.value.children[key[0]] == None:                            #直接插入空分支表
                self.root.value.children[key[0]] = self.make_leaf(key[1::],key[1::],value) #默认将key[0]作为拓展节点下分支结点的索引
                                                                                           #进行前缀压缩，去掉共同前缀作为下一步索引的前缀值
                node.value.children['value'] = False                                #插入新的叶子节点后，更新结点状态
                return
            else:                                                                   #root节点下branch表发生冲突，将冲突的节点位置作为参数进行递归
                self.root.value.children[key[0]] =  self.add_node(self.root.value.children[key[0]],key[1::],value)
                return
        father = node
        index = self.diff(father,key)                                               #将key值与父节点的前缀字符比较，index作为在当前拓展节点定位branch表位置的索引
        prefix = key[:index:]                                                       #共同前缀
        new_key = key[index::]                                                      #除去共同前缀后的剩余字符

        if index != len(father.prefix) and index < len(father.prefix):              #相同字符数不等于共同前缀长度，则代表新节点与father节点没有共同前缀，发生冲突

            if father.type == 'extension':                                          #extension冲突
                return self.pre_extension(father,prefix,new_key,index,value)        #创建新的拓展节点
            elif father.type == 'leaf':                                             #leaf冲突
                return self.pro_extension(father,prefix,new_key,index,value)        #创建新的拓展节点

        else:                                                                       #进入拓展的branch结点中向下遍历
            if father.value.children[key[index]] == None:                           #判断拓展节点下的branch对应key的value是否为空，为空，则添加leaf节点
                father.value.children[key[index]] = self.make_leaf(key[index+1::],key[index])

                father.value.children['value'] = False                              #插入新的leaf节点后更新结点
                return father
            else:                                                                   #发生字符表冲突，向下延展拓展结点
                father = self.add_node(father.value.children[key[index]],new_key,value)
                return father


    def pre_extension(self,node,prefix,key,index,value):                            #向前添加拓展节点
        node_new_prefix = node.prefix[index+1::]

        tmp_node = self.make_extension()                                            #创建新的拓展节点
        tmp_node.prefix = prefix                                                    #写入共同前缀
        tmp_node.value.children[node.prefix[index]] = node                          #将旧的拓展节点插入branch表中
        tmp_node.value.children[node.prefix[index]].prefix = node_new_prefix        #修改旧的拓展节点的共同前缀
        tmp_node.value.children[key[0]] = self.make_leaf(key[1::],key[0],value)     #插入叶子节点
        return tmp_node                                                             #返回新的拓展


    def pro_extension(self,node,prefix,key,index,value):                            #向后添加拓展节点
        leaf = node
        tmp_node = self.make_extension()
        tmp_node.prefix = prefix
        tmp_node.value.children[leaf.key_end[index]] = leaf
        tmp_node.value.children[leaf.key_end[index]].key_end = leaf.key_end[index+1::]  #产生共同前缀，leaf节点的key-end发生改变
        tmp_node.value.children[key[0]] = self.make_leaf(key[1::],key[0],value)
        return tmp_node


    def make_leaf(self,key,profix,value):                                           #创建叶节点
        tmp_node = Leaf_node()
        tmp_node.key_end = key
        tmp_node.prefix = profix
        tmp_node.value = value                                                         # 添加叶子节点的值和hash
        tmp_node.node_value = hashlib.sha256(value.encode('utf-8')).hexdigest()        #对数据进行hash
        tmp_node.node_hash = hashlib.sha256(str(tmp_node).encode('utf-8')).hexdigest() #对整个节点进行hash
        return tmp_node


    def make_extension(self):                                                       #创建拓展节点
        tmp_node = Extension_node()
        return tmp_node


    def diff(self,node,key):
        if len(key) < len(node.prefix):
            lenth = len(key)
        else:
            lenth = len(node.prefix)
        count = 0
        while count < lenth:
            if node.prefix[count] != key[count]:
                return count
            count+=1
        return count


    def traverse_search(self,node,index):                                           #遍历MPT树查询

        result_node = None

        for key in  node.value.children:                                            #遍历当前拓展节点的分支表

            if key == 'value':                                                      #检测终止标志则终止
                break

            if node.value.children[key] == None:                                    #检索到空值则继续
                continue

            if node.value.children[key].type == 'leaf':                             #检索到叶子节点，对比key-end和索引值
                if index[1::] == node.value.children[key].key_end:                  #如果匹配则返回该节点，否则继续检索
                    result_node =  node.value.children[key]
                    break
                else:
                    continue

            elif node.value.children[key].type == 'extension':                      #检索到拓展结点，进入到该节点的分支表
                short_key = index[len(node.value.children[key].prefix)+1::]         #记录去除该拓展节点的共同前缀后剩余的索引值
                result_node = self.traverse_search(node.value.children[key],short_key)#递归向下
                if result_node != None:
                    break
        return result_node                                                          #返回节点的索引


    def update_tree(self,node):
        tmp_str = ''
        if node.value.children['value'] == True:                                    #已更新则直接返回当前值
            return node.node_value
        for key in node.value.children:
            if key == 'value':
                break
            if node.value.children[key] == None:
                continue
            if node.value.children[key].type == 'leaf':
                tmp_str = tmp_str + node.value.children[key].node_value
            elif node.value.children[key].type == 'extension':
                tmp_str = tmp_str + self.update_tree(node.value.children[key])
        node.value.children['value'] = True                                         #节点修改状态
        node.node_value = hashlib.sha256(tmp_str.encode()).hexdigest()              #更新节点value、hash值
        node.node_hash = hashlib.sha256(str(node).encode()).hexdigest()
        print('prefix:',node.prefix)
        print('node_value:',node.node_value)
        return node.node_value


    def delete_node(self,node,hash):                                                #删除节点，使需要删除的节点对应的branch位置设为None
        for key in node.value.children:
            if key == 'value':
                break
            if node.value.children[key] == None:
                continue
            if node.value.children[key].type == 'leaf':
                if hash[1::] == node.value.children[key].key_end:
                    del node.value.children[key]
                    node.value.children[key] = None
                    return True
                else:
                    continue
            elif node.value.children[key].type == 'extension':
                short_hash = hash[len(node.value.children[key].prefix) + 1::]
                if short_hash == '':
                    del node.value.children[key]
                    node.value.children[key] = None
                    print('delete')
                    return True
                elif self.delete_node(node.value.children[key],short_hash):
                    return True


    def add(self,key,value,node=None):                                              #增操作
        if node == None:
            node = self.root
        self.add_node(node,key,value)
        self.update_tree(self.root)


    def delete(self,key):                                                           #删操作
        print('delete from str')
        self.delete_node(self.root,key)
        self.update_tree(self.root)


    def update(self,index,value):                                                   #改操作
        if type(index) == str:
            tmp_node = self.traverse_search(self.root,index)
            tmp_node.value = value
            tmp_node.node_value = hashlib.sha256(value.encode('utf-8')).hexdigest()
            tmp_node.node_hash = hashlib.sha256(str(tmp_node).encode('utf-8')).hexdigest()
        else:
            index.value = value
            index.node_value = hashlib.sha256(value.encode('utf-8')).hexdigest()
            index.node_hash = hashlib.sha256(str(index).encode('utf-8')).hexdigest()
        self.update_tree(tree.root)


    def search(self,index):                                                         #查操作
        if type(index) == str:
            return self.traverse_search(self.root,index).value
        else:
            return index.value


    def drop_all_value(self,node=None):
        if node == None:
            node = self.root
        for key in node.value.children:
            if key == 'value':
                break
            if node.value.children[key] == None:
                continue
            if node.value.children[key].type == 'leaf':
                del node.value.children[key].value
                node.value.children[key].value = None
            elif node.value.children[key].type == 'extension':
                self.drop_all_value(node.value.children[key])


    def drop_tree(self):
        self.update_tree(self.root)
        self.value = self.root.node_value
        self.hash = self.root.node_hash
        del self.root
        self.root = None
