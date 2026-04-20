class HashUtils:
    """
    实现Java版本的哈希算法
    """
    C1_32 = -862048943
    C2_32 = 461845907
    R1_32 = 15
    R2_32 = 13
    M_32 = 5
    N_32 = -430675100
    DEFAULT_SEED = 104729
    
    @staticmethod
    def hash32(data):
        """
        计算字符串的32位哈希值
        """
        if isinstance(data, str):
            origin = data.encode('utf-8')
            return HashUtils._hash32(origin, 0, len(origin), HashUtils.DEFAULT_SEED)
        elif isinstance(data, bytes):
            return HashUtils._hash32(data, 0, len(data), HashUtils.DEFAULT_SEED)
        else:
            raise TypeError("data must be str or bytes")
    
    @staticmethod
    def _hash32(data, offset, length, seed):
        """
        内部哈希计算方法
        """
        hash_val = seed
        nblocks = length >> 2  # 相当于除以4
        idx = 0
        
        for idx in range(nblocks):
            i = idx << 2  # 相当于乘以4
            # 构建32位整数
            k = (data[offset + i] & 0xFF) | \
                ((data[offset + i + 1] & 0xFF) << 8) | \
                ((data[offset + i + 2] & 0xFF) << 16) | \
                ((data[offset + i + 3] & 0xFF) << 24)
            # 确保k是32位整数
            k &= 0xFFFFFFFF
            hash_val = HashUtils._mix32(k, hash_val)
        
        idx = nblocks << 2
        k1 = 0
        
        if length - idx == 3:
            k1 ^= (data[offset + idx + 2] << 16)
            k1 ^= (data[offset + idx + 1] << 8)
            hash_val = HashUtils._get_hash(data, offset, hash_val, idx, k1)
        elif length - idx == 2:
            k1 ^= (data[offset + idx + 1] << 8)
            hash_val = HashUtils._get_hash(data, offset, hash_val, idx, k1)
        elif length - idx == 1:
            hash_val = HashUtils._get_hash(data, offset, hash_val, idx, k1)
        
        return HashUtils._fmix32(length, hash_val)
    
    @staticmethod
    def _get_hash(data, offset, hash_val, idx, k1):
        """
        获取哈希值
        """
        k1 ^= data[offset + idx]
        k1 &= 0xFFFFFFFF
        k1 *= HashUtils.C1_32
        k1 &= 0xFFFFFFFF
        k1 = HashUtils._rotate_left(k1, HashUtils.R1_32)
        k1 *= HashUtils.C2_32
        k1 &= 0xFFFFFFFF
        hash_val ^= k1
        hash_val &= 0xFFFFFFFF
        return hash_val
    
    @staticmethod
    def _mix32(k, hash_val):
        """
        混合哈希值
        """
        k *= HashUtils.C1_32
        k &= 0xFFFFFFFF
        k = HashUtils._rotate_left(k, HashUtils.R1_32)
        k *= HashUtils.C2_32
        k &= 0xFFFFFFFF
        hash_val ^= k
        hash_val &= 0xFFFFFFFF
        result = HashUtils._rotate_left(hash_val, HashUtils.R2_32) * HashUtils.M_32 + HashUtils.N_32
        return result & 0xFFFFFFFF
    
    @staticmethod
    def _fmix32(length, hash_val):
        """
        最终混合哈希值
        """
        hash_val ^= length
        hash_val &= 0xFFFFFFFF
        hash_val ^= (hash_val >> 16)
        hash_val &= 0xFFFFFFFF
        hash_val *= -2048144789
        hash_val &= 0xFFFFFFFF
        hash_val ^= (hash_val >> 13)
        hash_val &= 0xFFFFFFFF
        hash_val *= -1028477387
        hash_val &= 0xFFFFFFFF
        hash_val ^= (hash_val >> 16)
        hash_val &= 0xFFFFFFFF
        return hash_val
    
    @staticmethod
    def _rotate_left(x, n):
        """
        左旋转操作
        """
        return ((x << n) & 0xFFFFFFFF) | (x >> (32 - n))

class CustNoShardingUtil:
    """
    根据custNo计算分片ID
    """
    @staticmethod
    def determine_sharding_id_by_cust_no(cust_no, total_sharding_table_number):
        """
        根据custNo计算分片ID
        """
        hash_key = HashUtils.hash32(cust_no)
        if hash_key < 0:
            hash_key = -hash_key
        
        sharding_number = (hash_key % total_sharding_table_number) + 1
        sharding_id = "0000" + str(sharding_number)
        sharding_id = sharding_id[-4:]
        
        return sharding_id
    
    @staticmethod
    def calculate_hash(cust_no, total_sharding_table_number=8):
        """
        计算custNo的哈希值，返回1-8之间的整数
        """
        hash_key = HashUtils.hash32(cust_no)
        if hash_key < 0:
            hash_key = -hash_key
        
        return (hash_key % total_sharding_table_number) + 1