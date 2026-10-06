"""Minimal exact-source harness for StewardRail.

It is intentionally not a replacement for GenLayer Direct Mode. It executes the
exact deployable Python files and models message sender, payable value, balances,
nondeterministic web/LLM calls and `emit(on="finalized")` queues. The handoff
requires the same cases to be re-run with official tooling before submission.
"""
from __future__ import annotations
import copy, json, sys, types

class TreeMap(dict):
    def __class_getitem__(cls,item): return cls
class DynArray(list):
    def __class_getitem__(cls,item): return cls
def u256(value=0): return int(value)
def Address(value):
    text=str(value)
    if not text.startswith('0x') or len(text)!=42: raise ValueError('invalid address '+text)
    int(text[2:],16); return text

class _Write:
    def __new__(cls,fn): return fn
    @staticmethod
    def payable(fn): return fn
class _Public:
    write=_Write
    @staticmethod
    def view(fn): return fn
class _Response:
    def __init__(self,body): self.body=body

class Runtime:
    def __init__(self):
        self.contracts={}; self.sender='0x'+'0'*40; self.current=None; self.value=0
        self.now=1_700_000_000; self.web={}; self.model=lambda p:{'verdict':'refuse','confidence':100,'reason':'default'}
        self.balances={}; self.transfers=[]; self.finalized=[]; self.prompts=[]

    def state(self): return {a:copy.deepcopy(o.__dict__) for a,o in self.contracts.items()}
    def call(self,address,method,*args,sender=None,value=0):
        address=str(address).lower(); sender=(sender or self.sender).lower()
        snap=(self.state(),dict(self.balances),list(self.transfers),list(self.finalized))
        old=(self.sender,self.current,self.value); self.sender,self.current,self.value=sender,address,int(value)
        if int(value)>0:
            if self.balances.get(sender,0)<int(value):
                self.sender,self.current,self.value=old
                raise Exception('insufficient sender balance')
            self.balances[sender]=self.balances.get(sender,0)-int(value)
            self.balances[address]=self.balances.get(address,0)+int(value)
        try: return getattr(self.contracts[address],method)(*args)
        except Exception:
            states,bals,transfers,finalized=snap; self.balances=bals; self.transfers=transfers; self.finalized=finalized
            for a,d in states.items(): self.contracts[a].__dict__.clear(); self.contracts[a].__dict__.update(d)
            raise
        finally: self.sender,self.current,self.value=old

    def flush_finalized(self,limit=100):
        count=0
        while self.finalized:
            if count>=limit: raise RuntimeError('finalized message loop')
            source,target,method,args,value=self.finalized.pop(0)
            self.call(target,method,*args,sender=source,value=value); count+=1
        return count

    def transfer(self,to,amount):
        source=self.current; to=str(to).lower(); amount=int(amount)
        if self.balances.get(source,0)<amount: raise Exception('insufficient balance')
        self.balances[source]-=amount; self.balances[to]=self.balances.get(to,0)+amount
        self.transfers.append((source,to,amount))

    def make_gl(self):
        rt=self
        class Contract:
            def __init_subclass__(cls,**kw): super().__init_subclass__(**kw)
            @property
            def balance(self): return u256(rt.balances.get(self.__dict__.get('_stub_address',''),0))
            def __getattr__(self,name):
                ann={}
                for k in type(self).__mro__: ann.update(getattr(k,'__annotations__',{}))
                if name in ann:
                    kind=ann[name]; val=kind() if kind in (TreeMap,DynArray) else (0 if kind is u256 else '')
                    object.__setattr__(self,name,val); return val
                raise AttributeError(name)
        class Message:
            @property
            def sender_address(self): return Address(rt.sender)
            @property
            def origin_address(self): return Address(rt.sender)
            @property
            def contract_address(self): return Address(rt.current)
            @property
            def value(self): return u256(rt.value)
            @property
            def chain_id(self): return u256(61999)
        class Web:
            @staticmethod
            def get(uri):
                if uri not in rt.web: raise Exception('unmocked web '+uri)
                return _Response(rt.web[uri])
        class Nondet:
            web=Web
            @staticmethod
            def exec_prompt(prompt,response_format=None):
                rt.prompts.append(prompt); ans=rt.model(prompt)
                return ans if response_format=='json' else json.dumps(ans)
        class Vm:
            UserError=Exception
            @staticmethod
            def run_nondet(leader,validator,compare_user_errors=True):
                result=leader()
                if not validator(result): raise Exception('validators disagreed')
                return result
        class Emitter:
            def __init__(self,target,on,value=0): self.target=str(target).lower();self.on=on;self.value=int(value)
            def __getattr__(self,name):
                def send(*args):
                    if self.on!='finalized': raise Exception('stub only accepts finalized messages')
                    rt.finalized.append((rt.current,self.target,name,args,self.value))
                return send
        class Proxy:
            def __init__(self,target): self.target=str(target).lower()
            def view(self): return rt.contracts[self.target]
            def emit(self,on='finalized',value=0): return Emitter(self.target,on,value)
        class Evm:
            @staticmethod
            def contract_interface(cls):
                class Iface:
                    def __init__(self,address): self.address=str(address).lower()
                    def emit_transfer(self,value=0): rt.transfer(self.address,int(value))
                return Iface
        return types.SimpleNamespace(Contract=Contract,public=_Public,message=Message(),nondet=Nondet,vm=Vm,evm=Evm(),get_contract_at=lambda a:Proxy(a))

    def clock_module(self):
        rt=self
        class DT:
            @staticmethod
            def now(): return types.SimpleNamespace(timestamp=lambda:float(rt.now))
        return types.SimpleNamespace(datetime=DT)


def load(path,runtime):
    gl=runtime.make_gl(); fake=types.ModuleType('genlayer')
    for k,v in {'gl':gl,'Address':Address,'u256':u256,'TreeMap':TreeMap,'DynArray':DynArray}.items(): setattr(fake,k,v)
    fake.__all__=['gl','Address','u256','TreeMap','DynArray']; sys.modules['genlayer']=fake
    ns={'__name__':'steward_contract_under_test'}
    source=open(path).read(); exec(compile(source,path,'exec',dont_inherit=True),ns); ns['datetime']=runtime.clock_module(); return ns

def deploy(runtime,ns,cls,address,*args,sender=None):
    address=str(address).lower(); old=(runtime.sender,runtime.current)
    runtime.sender=(sender or runtime.sender).lower();runtime.current=address
    obj=ns[cls].__new__(ns[cls]);obj.__dict__['_stub_address']=address
    try: ns[cls].__init__(obj,*args)
    finally: runtime.sender,runtime.current=old
    runtime.contracts[address]=obj;runtime.balances.setdefault(address,0);return obj
