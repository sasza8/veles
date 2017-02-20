# Standing in the rain
# The cold and angry rain
# In a long white dress
# A girl without a name

import asyncio
import msgpack
from asrv.srv import BaseLister
from messages import messages


class ProtocolError(Exception):
    pass

class GetSub:
    def __init__(self, conn, qid, obj):
        self.conn = conn
        self.qid = qid
        self.obj = obj

    def kill(self):
        self.obj.remove_sub(self)

    def obj_changed(self):
        self.conn.send_obj_reply(self.qid, self.obj)

    def obj_gone(self):
        if self.qid in self.conn.subs:
            del self.conn.subs[self.qid]
        self.conn.send_obj_gone(self.qid)


class GetDataSub:
    def __init__(self, conn, qid, obj, key):
        self.conn = conn
        self.qid = qid
        self.obj = obj
        self.key = key

    def kill(self):
        self.obj.remove_data_sub(self)

    def data_changed(self, data):
        self.conn.send_obj_data_reply(self.qid, data)

    def obj_gone(self):
        if self.qid in self.conn.subs:
            del self.conn.subs[self.qid]
        self.conn.send_obj_gone(self.qid)


class Lister(BaseLister):
    def __init__(self, conn, qid, srv, obj, pos, tags):
        self.conn = conn
        self.qid = qid
        super().__init__(srv, obj, pos, tags)

    def list_changed(self, new, gone):
        self.conn.send_list_reply(self.qid, new, gone)

    def obj_gone(self):
        if self.qid in self.conn.subs:
            del self.conn.subs[self.qid]
        self.conn.send_obj_gone(self.qid)


class Proto(asyncio.Protocol):
    def __init__(self, srv):
        self.srv = srv
        self.subs = {}

    def connection_made(self, transport):
        self.transport = transport
        self.cid = self.srv.new_conn(self)
        self.packer = msgpack.Packer(use_bin_type=True)
        self.unpacker = msgpack.Unpacker(encoding='utf-8')

    def data_received(self, data):
        self.unpacker.feed(data)
        while True:
            try:
                msg = messages.MsgpackMsg.loads(self.unpacker)
                self.handle_msg(msg)
            except msgpack.OutOfData:
                return

    def handle_msg(self, msg):
        handlers = {
            'create': self.msg_create,
            'modify': self.msg_modify,
            'delete': self.msg_delete,
            'list': self.msg_list,
            'get': self.msg_get,
            'get_data': self.msg_get_data,
            'get_bin': self.msg_get_bin,
            'mthd_run': self.msg_mthd_run,
            'unsub': self.msg_unsub,
            'mthd_done': self.msg_mthd_done,
            'proc_done': self.msg_proc_done,
            'mthd_reg': self.msg_mthd_reg,
            'proc_reg': self.msg_proc_reg,
        }
        try:
            handlers[msg.msg_type](msg)
        except ProtocolError as e:
            self.send_msg(messages.MsgProtoError(
                error=e.args[0],
            ))

    def connection_lost(self, ex):
        for qid, sub in self.subs.items():
            sub.kill()
        self.srv.remove_conn(self)

    def send_msg(self, msg):
        self.transport.write(msg.dumps(self.packer))

    def msg_create(self, msg):
        self.srv.create(
            msg.id,
            msg.parent,
            tags=msg.tags,
            attr=msg.attr,
            data=msg.data,
            bindata=msg.bindata,
            pos=(msg.pos_start,msg.pos_end),
        )
        if msg.rid is not None:
            self.send_msg(messages.MsgAck(
                rid=msg.rid,
            ))

    def msg_modify(self, msg):
        # XXX
        raise NotImplementedError

    def msg_delete(self, msg):
        objs = msg.ids
        for obj in objs:
            if not isinstance(obj, bytes) or len(obj) != 24:
                self.protoerr('obj is not valid id')
        for obj in objs:
            self.srv.delete(obj)
        if msg.rid is not None:
            self.send_msg(messages.MsgAck(
                rid=msg.rid,
            ))

    def msg_list(self, msg):
        qid = msg.qid
        if qid in self.subs:
            raise ProtocoloError('qid already in use')
        tagsets = msg.tags
        lister = Lister(self, qid, self.srv, msg.parent, (msg.pos_start, msg.pos_end), tagsets)
        self.srv.run_lister(lister, msg.sub)
        if msg.sub:
            self.subs[qid] = lister

    def msg_get(self, msg):
        qid = msg.qid
        if qid in self.subs:
            raise ProtocoloError('qid already in use')
        obj = self.srv.get(msg.id)
        if obj is None:
            self.send_msg(messages.MsgObjGone(
                qid=qid,
            ))
        else:
            self.send_obj_reply(qid, obj)
            if msg.sub:
                sub = GetSub(self, qid, obj)
                self.subs[qid] = sub
                obj.add_sub(sub)

    def msg_get_data(self, msg):
        obj = self.getid(msg, 'id')
        sub = self.getfbool(msg, 'sub')
        qid = self.getnint(msg, 'qid')
        key = self.getstr(msg, 'key')
        if qid in self.subs:
            raise ProtocoloError('qid already in use')
        obj = self.srv.get(obj)
        if obj is None:
            self.send_msg({
                'type': 'obj_gone',
                'qid': qid,
            })
        else:
            data = self.srv.get_data(obj, key)
            self.send_obj_data_reply(qid, data)
            if sub:
                sub = GetDataSub(self, qid, obj, key)
                self.subs[qid] = sub
                obj.add_data_sub(sub)

    def msg_get_bin(self, msg):
        # XXX
        raise NotImplementedError

    def msg_unsub(self, msg):
        qid = self.getnint(msg, 'qid')
        if qid in self.subs:
            self.subs[qid].kill()
            del self.subs[qid]
        self.send_msg({
            'type': 'sub_gone',
            'qid': qid,
        })

    def msg_mthd_run(self, msg):
        # XXX
        raise NotImplementedError

    def msg_mthd_done(self, msg):
        # XXX
        raise NotImplementedError

    def msg_proc_done(self, msg):
        # XXX
        raise NotImplementedError

    def msg_mthd_reg(self, msg):
        # XXX
        raise NotImplementedError

    def msg_proc_reg(self, msg):
        # XXX
        raise NotImplementedError

    def send_obj_reply(self, qid, obj):
        self.send_msg(messages.MsgGetReply(
            qid=qid,
            id=obj.id,
            parent=obj.parent.id if obj.parent is not None else None,
            pos_start=obj.pos[0],
            pos_end=obj.pos[1],
            tags=list(obj.tags),
            attr=obj.attr,
            data=list(obj.data),
            bindata=obj.bindata,
        ))

    def send_list_reply(self, qid, new, gone):
        res = []
        for obj in new:
            res.append({
                'id': obj.id,
                'gone': False,
                'parent': obj.parent.id if obj.parent is not None else None,
                'pos_start': obj.pos[0],
                'pos_end': obj.pos[1],
                'tags': list(obj.tags),
                'attr': obj.attr,
                'data': list(obj.data),
                'bindata': obj.bindata,
            })
        for id in gone:
            res.append({
                'id': id,
                'gone': True,
            })
        self.send_msg(messages.MsgListReply(
            objs=res,
            qid=qid,
        ))

    def send_obj_gone(self, qid):
        self.send_msg(messages.MsgObjGone(
            qid=qid,
        ))

@asyncio.coroutine
def unix_server(srv, path):
    return (yield from srv.loop.create_unix_server(lambda: Proto(srv), path))

@asyncio.coroutine
def tcp_server(srv, ip, port):
    return (yield from srv.loop.create_server(lambda: Proto(srv), ip, port))
