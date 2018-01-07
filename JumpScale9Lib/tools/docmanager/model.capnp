@0xd99b12c2d2d111c5;

struct Doc {
    uid @0 :Text;
    suid @1 :Text;  #shortuid
    name @2 :Text;
    description @3 :Text;
    starred @4 :Bool;
    modTime @5 :UInt32;
    docs @6 :List(GDoc);
    struct GDoc{
        id @0 :Text;
        webContentLink @1 :Text;
        webViewLink @2 :Text;
        modTime @3 :UInt32;
        version @4 :Text;
        parents @5 :List(Text);
    }

    comments @7 :List(Comment);
    struct Comment{
        owner @0 :Text;
        comment @1 :Text;
        modTime @2 :UInt32;
    }

    labels @8 :List(Text);


    type @9: Type;
    enum Type {
        xlsx   @0;
        docx   @1;
        pdf    @2;
    }

    type @10: State;
    enum State {
        active   @0;
        beta   @1;
        trash    @2;
        archive    @3;
    }

}
