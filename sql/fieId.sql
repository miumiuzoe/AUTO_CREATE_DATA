-- 查询协议候选结果，必须至少返回 OBJ_GUID 和 SYS_ID

select * from `OBJECT` o where o.OBJ_ENGNAME = :obj_engname;


-- 根据选中的 OBJ_GUID 查询协议字段信息

SELECT iof.*
FROM INPUTOBJECTFIELD iof
JOIN INPUTOBJECT i 
  ON i.IOBJ_GUID = iof.IOBJ_GUID
JOIN OBJECT o 
  ON o.OBJ_GUID = i.OBJ_GUID
WHERE o.OBJ_GUID = :obj_guid
  AND o.OBJ_ENGNAME = :obj_engname
  AND iof.IOF_KEYNAME <> 'Consfield'
  AND iof.IOF_STATUS = 0 order by iof.IOF_ID asc;