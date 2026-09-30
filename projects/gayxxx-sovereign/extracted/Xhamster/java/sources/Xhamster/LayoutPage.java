package Xhamster;

/* JADX INFO: compiled from: Xhamster.kt */
/* JADX INFO: loaded from: classes.dex */
@kotlin.Metadata(d1 = {"\u0000&\n\u0002\u0018\u0002\n\u0002\u0010\u0000\n\u0000\n\u0002\u0018\u0002\n\u0002\b\u0007\n\u0002\u0010\u000b\n\u0002\b\u0002\n\u0002\u0010\b\n\u0000\n\u0002\u0010\u000e\n\u0000\b\u0086\b\u0018\u00002\u00020\u0001B\u0013\u0012\n\b\u0003\u0010\u0002\u001a\u0004\u0018\u00010\u0003¢\u0006\u0004\b\u0004\u0010\u0005J\u000b\u0010\b\u001a\u0004\u0018\u00010\u0003HÆ\u0003J\u0015\u0010\t\u001a\u00020\u00002\n\b\u0003\u0010\u0002\u001a\u0004\u0018\u00010\u0003HÆ\u0001J\u0014\u0010\n\u001a\u00020\u000b2\b\u0010\f\u001a\u0004\u0018\u00010\u0001HÖ\u0083\u0004J\n\u0010\r\u001a\u00020\u000eHÖ\u0081\u0004J\n\u0010\u000f\u001a\u00020\u0010HÖ\u0081\u0004R\u0018\u0010\u0002\u001a\u0004\u0018\u00010\u00038\u0006X\u0087\u0004¢\u0006\b\n\u0000\u001a\u0004\b\u0006\u0010\u0007¨\u0006\u0011"}, d2 = {"LXhamster/LayoutPage;", "", "videoListProps", "LXhamster/VideoListProps;", "<init>", "(LXhamster/VideoListProps;)V", "getVideoListProps", "()LXhamster/VideoListProps;", "component1", "copy", "equals", "", "other", "hashCode", "", "toString", "", "Xhamster"}, k = 1, mv = {2, 3, 0}, xi = 48)
public final /* data */ class LayoutPage {

    @com.fasterxml.jackson.annotation.JsonProperty("videoListProps")
    @org.jetbrains.annotations.Nullable
    private final Xhamster.VideoListProps videoListProps;

    /* JADX WARN: Illegal instructions before constructor call */
    public LayoutPage() {
        Xhamster.VideoListProps videoListProps = null;
        this(videoListProps, 1, videoListProps);
    }

    public static /* synthetic */ Xhamster.LayoutPage copy$default(Xhamster.LayoutPage layoutPage, Xhamster.VideoListProps videoListProps, int i, java.lang.Object obj) {
        if ((i & 1) != 0) {
            videoListProps = layoutPage.videoListProps;
        }
        return layoutPage.copy(videoListProps);
    }

    @org.jetbrains.annotations.Nullable
    /* JADX INFO: renamed from: component1, reason: from getter */
    public final Xhamster.VideoListProps getVideoListProps() {
        return this.videoListProps;
    }

    @org.jetbrains.annotations.NotNull
    public final Xhamster.LayoutPage copy(@com.fasterxml.jackson.annotation.JsonProperty("videoListProps") @org.jetbrains.annotations.Nullable Xhamster.VideoListProps videoListProps) {
        return new Xhamster.LayoutPage(videoListProps);
    }

    public boolean equals(@org.jetbrains.annotations.Nullable java.lang.Object other) {
        if (this == other) {
            return true;
        }
        return (other instanceof Xhamster.LayoutPage) && kotlin.jvm.internal.Intrinsics.areEqual(this.videoListProps, ((Xhamster.LayoutPage) other).videoListProps);
    }

    public int hashCode() {
        if (this.videoListProps == null) {
            return 0;
        }
        return this.videoListProps.hashCode();
    }

    @org.jetbrains.annotations.NotNull
    public java.lang.String toString() {
        return "LayoutPage(videoListProps=" + this.videoListProps + ')';
    }

    public LayoutPage(@com.fasterxml.jackson.annotation.JsonProperty("videoListProps") @org.jetbrains.annotations.Nullable Xhamster.VideoListProps videoListProps) {
        this.videoListProps = videoListProps;
    }

    public /* synthetic */ LayoutPage(Xhamster.VideoListProps videoListProps, int i, kotlin.jvm.internal.DefaultConstructorMarker defaultConstructorMarker) {
        this((i & 1) != 0 ? null : videoListProps);
    }

    @org.jetbrains.annotations.Nullable
    public final Xhamster.VideoListProps getVideoListProps() {
        return this.videoListProps;
    }
}
